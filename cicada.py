import os
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass


#config | 配置对象
@dataclass
class Config:
    project_name: str
    domain: str
    server_ip: str
    git_url: str
    git_branch: str
    project_root: str
    repo_dir: str
    venv_dir: str
    static_root: str
    media_root: str
    service_name: str
    gunicorn_bind: str
    email: str
    use_mysql: bool

#show banner | 展示横幅
def show_banner():
    color_banner = "\033[1;38;2;234;77;98m"
    reset_banner = "\033[0m"

    banner = r"""
       ██████╗ ██╗ ██████╗ █████╗ ██████╗  █████╗
      ██╔════╝ ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗
      ██║      ██║██║     ███████║██║  ██║███████║
      ██║      ██║██║     ██╔══██║██║  ██║██╔══██║
      ╚██████╗ ██║╚██████╗██║  ██║██████╔╝██║  ██║
       ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝  v0.1.0

        CICADA: Command-line Integration for Continuous Automated Django Administration
        https://github.com/Vernaliza/CICADA
    """
    print("=" * 60)
    print(color_banner + banner + reset_banner)
    print("=" * 60)


#used to execute shell commands | 用于执行shell命令
def run(cmd: str, check: bool = True, cwd: str | None = None):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and result.returncode != 0:
        raise RuntimeError(f"命令执行失败：{cmd}")
    return result.returncode


#file writing | 文件写入
def write_file(path: str, content: str):
    Path(path).write_text(content, encoding="utf-8")
    print(f"已写入: {path}")


#auto find Django's wsgi module | 自动寻找Django的wsgi模块
def detect_wsgi_module(project_dir: str) -> str:
    candidates = list(Path(project_dir).glob("**/wsgi.py"))
    filtered = []
    for p in candidates:
        parts = set(p.parts)
        if ".venv" in parts or "venv" in parts or "site-packages" in parts:
            continue
        filtered.append(p)
    if not filtered:
        raise RuntimeError("未找到wsgi.py，请确认路径是否正确。")
    filtered.sort(key=lambda p: len(p.parts))
    p = filtered[0]
    return ".".join(p.relative_to(project_dir).with_suffix("").parts)


#read boolean input | 读取布尔值输入
def prompt_bool(msg: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    value = input(f"{msg} [{hint}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "1"}


#collect deployment parameters | 收集部署参数
def collect_config() -> Config:
    print("需要 root 权限运行。")

    project_name = input("0) 项目名: ").strip()
    if not project_name:
        raise SystemExit("项目名不能为空")

    domain = input("0) 域名（如 example.com）: ").strip()
    server_ip = input("0) 服务器 IP: ").strip()
    git_url = input("2) GitHub 仓库地址: ").strip()
    git_branch = input("2) Git 分支 [main]: ").strip() or "main"
    email = input("5) HTTPS 邮箱（certbot 用，可留空）: ").strip()
    use_mysql = prompt_bool("项目是否使用 MySQL 驱动 mysqlclient", default=False)

    project_root = f"/root/{project_name}"
    repo_dir = project_root
    venv_dir = f"{project_root}/venv"
    static_root = f"/var/www/{project_name}/static"
    media_root = f"/var/www/{project_name}/media"
    service_name = f"gunicorn_{project_name}"
    gunicorn_bind = "127.0.0.1:8000"

    return Config(
        project_name=project_name,
        domain=domain,
        server_ip=server_ip,
        git_url=git_url,
        git_branch=git_branch,
        project_root=project_root,
        repo_dir=repo_dir,
        venv_dir=venv_dir,
        static_root=static_root,
        media_root=media_root,
        service_name=service_name,
        gunicorn_bind=gunicorn_bind,
        email=email,
        use_mysql=use_mysql,
    )


#check root permission | 检查root权限
def ensure_root():
    if os.geteuid() != 0:
        raise SystemExit("请使用 sudo 或 root 运行此脚本。")


#这里往下是功能性函数了
#set up environment | 配置服务器环境
def setup_environment(cfg: Config):
    print("\n[1] 配置环境")
    run("apt update && apt upgrade -y")
    run("apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx")
    run("python3 -m pip install --upgrade pip")
    Path(cfg.project_root).mkdir(parents=True, exist_ok=True)
    if not Path(cfg.venv_dir).exists():
        run(f"python3 -m venv {cfg.venv_dir}")
    run(f"mkdir -p {cfg.static_root}")
    run(f"mkdir -p {cfg.media_root}")
    pip_install = f"{cfg.venv_dir}/bin/pip install django gunicorn psycopg2-binary"
    if cfg.use_mysql:
        pip_install += " mysqlclient"
    run(pip_install)
    print("环境配置完成。")


#clone GitHub project | 拉取项目
def clone_project(cfg: Config):
    print("\n[2] 项目上传（GitHub）")
    if not cfg.git_url:
        raise RuntimeError("Git仓库地址不能为空。")

    if Path(cfg.repo_dir).exists() and any(Path(cfg.repo_dir).iterdir()):
        git_dir = Path(cfg.repo_dir) / ".git"
        if git_dir.exists():
            print("检测到已有git项目，执行拉取更新。")
            run("git fetch --all", cwd=cfg.repo_dir)
            run(f"git checkout {cfg.git_branch}", cwd=cfg.repo_dir)
            run(f"git pull origin {cfg.git_branch}", cwd=cfg.repo_dir)
        else:
            raise RuntimeError(f"目录 {cfg.repo_dir} 已存在且非空，无法自动clone。")
    else:
        parent = str(Path(cfg.repo_dir).parent)
        Path(parent).mkdir(parents=True, exist_ok=True)
        run(f"git clone -b {cfg.git_branch} {cfg.git_url} {cfg.repo_dir}")

    req = Path(cfg.repo_dir) / "requirements.txt"
    if req.exists():#Actually, there may not necessarily be project dependency files | 其实不一定有项目依赖文件的
        run(f"{cfg.venv_dir}/bin/pip install -r requirements.txt", cwd=cfg.repo_dir)
    print("项目拉取完成。")


#configure Gunicorn | 配置 Gunicorn
def configure_gunicorn(cfg: Config):
    print("\n[3] Gunicorn自动配置")
    wsgi_module = detect_wsgi_module(cfg.repo_dir)
    gunicorn_test = f"{cfg.venv_dir}/bin/gunicorn --bind 0.0.0.0:8000 {wsgi_module}:application --daemon"
    kill_test = "pkill -f 'gunicorn --bind 0.0.0.0:8000' || true"

    service_content = f"""[Unit]
    Description=gunicorn daemon for {cfg.project_name}
    After=network.target
    
    [Service]
    User=root
    Group=www-data
    WorkingDirectory={cfg.repo_dir}
    ExecStart={cfg.venv_dir}/bin/gunicorn \\
        --workers 3 \\
        --bind {cfg.gunicorn_bind} \\
        {wsgi_module}:application
    Restart=always
    RestartSec=3
    
    [Install]
    WantedBy=multi-user.target
    """
    service_path = f"/etc/systemd/system/{cfg.service_name}.service"
    write_file(service_path, service_content)

    run(gunicorn_test)
    run(kill_test, check=False)
    run("systemctl daemon-reload")
    run(f"systemctl enable {cfg.service_name}")
    run(f"systemctl restart {cfg.service_name}")
    run(f"systemctl status {cfg.service_name} --no-pager", check=False)
    print(f"Gunicorn配置完成，服务名: {cfg.service_name}")


#configure Nginx | 配置 Nginx
def configure_nginx(cfg: Config):
    print("\n[4] Nginx 自动配置")
    server_names = " ".join([x for x in {cfg.domain, f'www.{cfg.domain}', cfg.server_ip} if x])
    nginx_content = f"""server {{
    listen 80;
    server_name {server_names};

    client_max_body_size 20M;

    location /static/ {{
        alias {cfg.static_root}/;
    }}

    location /media/ {{
        alias {cfg.media_root}/;
    }}

    location / {{
        proxy_pass http://{cfg.gunicorn_bind};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    available = f"/etc/nginx/sites-available/{cfg.project_name}"
    enabled = f"/etc/nginx/sites-enabled/{cfg.project_name}"
    write_file(available, nginx_content)

    default_site = Path("/etc/nginx/sites-enabled/default")
    if default_site.exists():
        default_site.unlink()
        print("已移除默认站点default")

    enabled_path = Path(enabled)
    if not enabled_path.exists():
        enabled_path.symlink_to(available)
        print(f"已启用站点: {enabled}")

    run("nginx -t")
    run("systemctl reload nginx")
    print("Nginx配置完成。")


#run optional django tasks | 执行Django管理命令，负责数据库迁移和收集静态文件
def run_optional_django_tasks(cfg: Config):
    manage_py = Path(cfg.repo_dir) / "manage.py"
    if not manage_py.exists():
        print("未找到manage.py，跳过migrate & collectstatic。")
        return
    py = f"{cfg.venv_dir}/bin/python"
    try:
        run(f"{py} manage.py migrate", cwd=cfg.repo_dir)
    except Exception as e:
        print(f"migrate失败，可稍后手动执行: {e}")
    try:
        run(f"{py} manage.py collectstatic --noinput", cwd=cfg.repo_dir)
    except Exception as e:
        print(f"collectstatic失败，可稍后手动执行: {e}")


#configure HTTPS | 申请HTTPS证书
def configure_https(cfg: Config):
    print("\n[5] HTTPS自动配置")
    if not cfg.domain:
        raise RuntimeError("域名不能为空，HTTPS 需要域名。")
    if not prompt_bool("请确认域名已解析到本机且80/443端口已放行，继续申请证书吗", default=False):
        print("已跳过HTTPS配置。")
        return
    email_part = f"--email {cfg.email}" if cfg.email else "--register-unsafely-without-email"
    run(f"certbot --nginx {email_part} --agree-tos --no-eff-email -d {cfg.domain} -d www.{cfg.domain}")
    run("certbot renew --dry-run", check=False)
    print("HTTPS配置完成。")


#show summary | 显示当前全部配置的摘要
def show_summary(cfg: Config):
    print("\n" + "=" * 60)
    print("部署信息")
    print(f"项目名: {cfg.project_name}")
    print(f"项目目录: {cfg.repo_dir}")
    print(f"域名: {cfg.domain}")
    print(f"IP: {cfg.server_ip}")
    print(f"Gunicorn 服务: {cfg.service_name}")
    print(f"Nginx 站点: /etc/nginx/sites-available/{cfg.project_name}")
    print("=" * 60)


#menu | 菜单
def menu(cfg: Config):
    actions = {
        "1": lambda: setup_environment(cfg),
        "2": lambda: clone_project(cfg),
        "3": lambda: configure_gunicorn(cfg),
        "4": lambda: configure_nginx(cfg),
        "5": lambda: configure_https(cfg),
        "6": lambda: run_optional_django_tasks(cfg),
        "7": lambda: (setup_environment(cfg), clone_project(cfg), run_optional_django_tasks(cfg), configure_gunicorn(cfg), configure_nginx(cfg), configure_https(cfg)),
        "8": lambda: show_summary(cfg),
    }
    while True:
        show_summary(cfg)
        print("请选择操作:")
        print("1) 配置环境")
        print("2) 项目拉取（GitHub）")
        print("3) Gunicorn自动配置")
        print("4) Nginx自动配置")
        print("5) HTTPS自动配置")
        print("6) 数据库迁移和收集静态文件")
        print("7) 全部执行 1 → 6")
        print("8) 展示当前配置")
        print("0) 退出")
        choice = input("输入编号: ").strip()
        if choice == "0":
            break
        action = actions.get(choice)
        if not action:
            print("无效选项，请重试。")
            continue
        try:
            action()
            print("\n操作完成。")
        except Exception as e:
            print(f"\n操作失败: {e}")


def main():
    show_banner()
    ensure_root()
    cfg = collect_config()
    menu(cfg)


if __name__ == "__main__":
    main()
