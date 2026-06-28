package main

import (
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"sync"
	"time"
)

// ============================================================
// 河南高考志愿填报 · 后端服务器
// 本地 JSON 文件存储 · 密码验证 · 多端同步
// ============================================================

var (
	dataFile string
	password string
	addr     string

	mu       sync.RWMutex
	saved    json.RawMessage // 存储的志愿数据
	modTime  time.Time       // 最后修改时间
	sessions = make(map[string]time.Time) // token → 过期时间
)

func main() {
	flag.StringVar(&addr, "addr", ":8080", "监听地址")
	flag.StringVar(&password, "password", "", "访问密码（也可通过 PASSWORD 环境变量设置）")
	flag.StringVar(&dataFile, "data", "volunteer_data.json", "数据文件路径")
	flag.Parse()

	if password == "" {
		password = os.Getenv("PASSWORD")
	}
	if password == "" {
		password = "gaokao2026"
	}

	// 加载已有数据
	if b, err := os.ReadFile(dataFile); err == nil {
		var raw json.RawMessage
		if json.Unmarshal(b, &raw) == nil {
			saved = raw
			modTime = time.Now()
		}
	}

	// 定时清理过期 session（每小时）
	go func() {
		for {
			time.Sleep(1 * time.Hour)
			mu.Lock()
			now := time.Now()
			for tok, exp := range sessions {
				if now.After(exp) {
					delete(sessions, tok)
				}
			}
			mu.Unlock()
		}
	}()

	// 路由
	http.HandleFunc("/api/auth", handleAuth)
	http.HandleFunc("/api/check", handleCheck)
	http.HandleFunc("/api/data", handleData)
	http.HandleFunc("/", handleStatic)

	// 打印启动信息
	log.SetFlags(0)
	log.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	log.Println("  🎓 河南高考志愿填报 · 同步服务器")
	log.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	log.Printf("  本机地址:  http://localhost%s", addr)
	for _, ip := range localIPs() {
		log.Printf("  局域网地址: http://%s%s", ip, addr)
	}
	log.Printf("  访问密码:  %s", password)
	log.Printf("  数据文件:  %s", dataFile)
	log.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	log.Println("  在浏览器打开上方地址即可使用。")
	log.Println("  手机/平板/其他电脑打开同一地址可自动同步。")
	log.Println()

	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("启动失败: %v", err)
	}
}

// ---------- 工具函数 ----------

func localIPs() []string {
	var ips []string
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return ips
	}
	for _, a := range addrs {
		if ipn, ok := a.(*net.IPNet); ok && !ipn.IP.IsLoopback() && ipn.IP.To4() != nil {
			ips = append(ips, ipn.IP.String())
		}
	}
	return ips
}

func hashPW(pw string) string {
	h := sha256.Sum256([]byte(pw))
	return hex.EncodeToString(h[:])
}

func makeToken() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func writeJSON(w http.ResponseWriter, v interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, code int, msg string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"ok":    false,
		"error": msg,
	})
}

// ---------- 鉴权 ----------

// checkAuth 验证请求是否携带有效 session
func checkAuth(r *http.Request) bool {
	tok := ""
	if c, err := r.Cookie("volunteer_session"); err == nil && c.Value != "" {
		tok = c.Value
	}
	if tok == "" {
		tok = r.Header.Get("X-Session")
	}
	if tok == "" {
		return false
	}

	mu.RLock()
	exp, ok := sessions[tok]
	mu.RUnlock()
	if !ok {
		return false
	}
	if time.Now().After(exp) {
		mu.Lock()
		delete(sessions, tok)
		mu.Unlock()
		return false
	}
	return true
}

// handleAuth POST /api/auth — 验证密码并签发 session
func handleAuth(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		writeError(w, 405, "method not allowed")
		return
	}

	var body struct {
		Password string `json:"password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, 400, "请求格式错误")
		return
	}

	expected := hashPW(password)
	actual := hashPW(body.Password)

	if subtle.ConstantTimeCompare([]byte(expected), []byte(actual)) != 1 {
		writeError(w, 401, "密码错误")
		return
	}

	tok := makeToken()
	exp := time.Now().Add(72 * time.Hour) // session 有效期 3 天

	mu.Lock()
	sessions[tok] = exp
	mu.Unlock()

	http.SetCookie(w, &http.Cookie{
		Name:     "volunteer_session",
		Value:    tok,
		Path:     "/",
		Expires:  exp,
		HttpOnly: false, // JS 需要读取此 cookie 进行 API 鉴权
		SameSite: http.SameSiteLaxMode,
	})

	writeJSON(w, map[string]interface{}{
		"ok":    true,
		"token": tok,
	})
}

// handleCheck GET /api/check — 检查是否已登录
func handleCheck(w http.ResponseWriter, r *http.Request) {
	authed := checkAuth(r)
	writeJSON(w, map[string]interface{}{
		"authenticated": authed,
	})
}

// ---------- 数据存取 ----------

// handleData 处理 GET/POST /api/data
func handleData(w http.ResponseWriter, r *http.Request) {
	if !checkAuth(r) {
		writeError(w, 401, "未登录，请先输入密码")
		return
	}

	switch r.Method {
	case "GET":
		handleGetData(w, r)
	case "POST":
		handlePostData(w, r)
	default:
		writeError(w, 405, "method not allowed")
	}
}

// handleGetData GET /api/data[?version=xxx] — 获取数据
func handleGetData(w http.ResponseWriter, r *http.Request) {
	clientVer := r.URL.Query().Get("version")

	mu.RLock()
	serverVer := fmt.Sprintf("%d", modTime.UnixMilli())
	mu.RUnlock()

	// 版本未变 → 304 Not Modified
	if clientVer != "" && clientVer == serverVer {
		w.WriteHeader(http.StatusNotModified)
		return
	}

	mu.RLock()
	raw := saved
	mu.RUnlock()

	result := map[string]interface{}{
		"version": serverVer,
	}
	if raw != nil {
		result["data"] = raw
	} else {
		result["data"] = nil
	}

	writeJSON(w, result)
}

// handlePostData POST /api/data — 保存数据
func handlePostData(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Data json.RawMessage `json:"data"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, 400, "请求格式错误")
		return
	}

	// 格式化后写入文件
	var obj interface{}
	if err := json.Unmarshal(body.Data, &obj); err != nil {
		writeError(w, 400, "数据格式错误")
		return
	}
	pretty, err := json.MarshalIndent(obj, "", "  ")
	if err != nil {
		writeError(w, 500, "数据编码失败")
		return
	}
	if err := os.WriteFile(dataFile, pretty, 0644); err != nil {
		writeError(w, 500, "写入文件失败: "+err.Error())
		return
	}

	now := time.Now()
	mu.Lock()
	saved = body.Data
	modTime = now
	mu.Unlock()

	version := fmt.Sprintf("%d", now.UnixMilli())
	writeJSON(w, map[string]interface{}{
		"ok":      true,
		"version": version,
	})
}

// ---------- 静态文件 ----------

func handleStatic(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/" || r.URL.Path == "/volunteer_form.html" {
		// 设置 no-cache 避免浏览器缓存旧版本
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.Header().Set("Pragma", "no-cache")
		w.Header().Set("Expires", "0")
		http.ServeFile(w, r, "volunteer_form.html")
		return
	}
	http.NotFound(w, r)
}
