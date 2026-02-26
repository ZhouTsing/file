#!/usr/bin/env python3
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
import socket
import platform
import datetime

app = FastAPI(
    title="IP Echo Service - Enhanced",
    description="高级IP回显服务，包含详细信息",
    version="1.0.0"
)

# 添加信任主机中间件（可选）
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 生产环境应该设置具体域名
)

#@app.get("/1", response_class=HTMLResponse)
async def root():
    """主页，返回HTML格式的说明"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IP Echo Service</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 { color: #333; }
            .endpoint {
                background-color: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            code {
                background-color: #f0f0f0;
                padding: 2px 5px;
                border-radius: 3px;
            }
            a {
                color: #007bff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>🌐 IP Echo Service</h1>
        <p>欢迎使用IP回显服务！以下是可用的端点：</p>
        
        <div class="endpoint">
            <h3><a href="/ip">/ip</a></h3>
            <p>返回客户端IP地址（纯文本格式）</p>
            <code>curl http://localhost:8000/ip</code>
        </div>
        
        <div class="endpoint">
            <h3><a href="/ip-json">/ip-json</a></h3>
            <p>返回客户端IP地址（JSON格式）</p>
            <code>curl http://localhost:8000/ip-json</code>
        </div>
        
        <div class="endpoint">
            <h3><a href="/ip-details">/ip-details</a></h3>
            <p>返回详细的IP信息</p>
            <code>curl http://localhost:8000/ip-details</code>
        </div>
        
        <div class="endpoint">
            <h3><a href="/ip-info">/ip-info</a></h3>
            <p>返回客户端IP和请求信息</p>
            <code>curl http://localhost:8000/ip-info</code>
        </div>
        
        <div class="endpoint">
            <h3><a href="/health">/health</a></h3>
            <p>健康检查端点</p>
            <code>curl http://localhost:8000/health</code>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/ip", response_class=PlainTextResponse)
async def get_ip_text(request: Request):
    """返回客户端IP地址（纯文本格式）"""
    return get_client_ip(request)

@app.get("/ip-json")
async def get_ip_json(request: Request):
    """返回客户端IP地址（JSON格式）"""
    return {"ip": get_client_ip(request)}

@app.get("/ip-details")
async def get_ip_details(request: Request):
    """返回详细的IP信息"""
    client_ip = get_client_ip(request)
    
    return {
        "client_info": {
            "ip": client_ip,
            "port": request.client.port if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "accept_language": request.headers.get("accept-language"),
            "accept_encoding": request.headers.get("accept-encoding"),
        },
        "proxy_info": {
            "x_forwarded_for": request.headers.get("x-forwarded-for"),
            "x_real_ip": request.headers.get("x-real-ip"),
            "x_forwarded_proto": request.headers.get("x-forwarded-proto"),
            "x_forwarded_host": request.headers.get("x-forwarded-host"),
        },
        "request_info": {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
    }

@app.get("/ip-info")
async def get_ip_info(request: Request):
    """返回客户端IP和基本请求信息"""
    client_ip = get_client_ip(request)
    
    return {
        "ip": client_ip,
        "request_time": datetime.datetime.utcnow().isoformat(),
        "user_agent": request.headers.get("user-agent"),
        "method": request.method,
        "path": request.url.path
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "server_info": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python_version": platform.python_version()
        }
    }

def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址
    考虑代理和负载均衡的情况
    """
    # 尝试从X-Forwarded-For获取
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # X-Forwarded-For格式: client, proxy1, proxy2
        # 取第一个IP作为客户端真实IP
        ip = x_forwarded_for.split(",")[0].strip()
        if ip and ip != "unknown":
            return ip
    
    # 尝试从X-Real-IP获取
    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip and x_real_ip != "unknown":
        return x_real_ip
    
    # 尝试从X-Forwarded获取
    x_forwarded = request.headers.get("x-forwarded")
    if x_forwarded:
        # 可能包含 IP 信息
        parts = x_forwarded.split(";")
        for part in parts:
            if "for=" in part:
                ip = part.split("for=")[1].strip()
                if ip:
                    return ip
    
    # 回退到直接连接的客户端IP
    if request.client:
        return request.client.host
    
    return "unknown"

# 添加错误处理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "请求的端点不存在",
            "available_endpoints": ["/", "/ip", "/ip-json", "/ip-details", "/ip-info", "/health"]
        }
    )

if __name__ == "__main__":
    print("启动IP Echo服务...")
    print("访问 http://localhost:8000 查看API文档")
    print("访问 http://localhost:8000/ip 获取IP地址")
    print("访问 http://localhost:8000/docs 查看Swagger文档")
