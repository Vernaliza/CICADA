#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
import json
from dataclasses import asdict
from pathlib import Path


CONFIG_FILE = Path("deploy_configs.json")


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
       ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝

        CICADA: Command-line Integration for Continuous Automated Django Administration
        https://github.com/Vernaliza/CICADA
    """
    print("=" * 60)
    print(f"{color_banner}{banner}{reset_banner}")
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


#bulid a new config | 创建新配置
def build_config_from_input() -> Config:
    print("需要root权限运行。")
    print("新建部署配置：")

    project_name = input("1.项目名：").strip()
    if not project_name:
        raise SystemExit("项目名不能为空")

    domain = input("2.域名（如example.com）: ").strip()
    server_ip = input("3.服务器IP：").strip()
    git_url = input("4.GitHub仓库地址：").strip()
    git_branch = input("5.Git分支[main]: ").strip() or "main"
    email = input("6.HTTPS邮箱（certbot使用，可留空）：").strip()
    use_mysql = prompt_bool("7.项目是否使用MySQL驱动mysqlclient", default=False)

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


#读取配置文件
def load_config_list() -> list[dict]:
    if not CONFIG_FILE.exists():
        return []

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass

    return []


#save config list | 将配置列表写入文件
def save_config_list(configs: list[dict]) -> None:
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(configs, f, ensure_ascii=False, indent=2)


#choose config | 选择配置
def choose_config(configs: list[dict]) -> dict:
    if not configs:
        raise SystemExit("当前没有可用配置，请先创建。")

    print("\n已有配置：")
    for i, cfg in enumerate(configs, start=1):
        print(f"{i}) {cfg['project_name']}  [{cfg.get('domain', '')}]")

    while True:
        raw = input("请选择配置编号：").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(configs):
                return configs[idx]
        print("输入无效，请重新输入。")


#delete config | 删除配置
def delete_config(configs: list[dict]) -> list[dict]:
    if not configs:
        print("当前没有可删除的配置。")
        return configs

    print("\n可删除配置：")
    for i, cfg in enumerate(configs, start=1):
        print(f"{i}) {cfg['project_name']}  [{cfg.get('domain', '')}]")

    while True:
        raw = input("请输入要删除的配置编号：").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(configs):
                removed = configs.pop(idx)
                save_config_list(configs)
                print(f"已删除配置：{removed['project_name']}")
                return configs
        print("输入无效，请重新输入。")
#collect deployment parameters | 收集部署参数


#the ui of config | 配置文件界面
def collect_config() -> Config:
    while True:
        configs = load_config_list()

        print("\n配置管理")
        print("1) 从配置列表加载")
        print("2) 创建新配置")
        print("3) 删除配置")
        print("4) 退出")

        choice = input("请选择操作 [1/2/3/4]: ").strip()

        if choice == "1":
            selected = choose_config(configs)
            print(f"已加载配置：{selected['project_name']}")
            return Config(**selected)

        elif choice == "2":
            cfg = build_config_from_input()

            existing_index = next(
                (i for i, item in enumerate(configs) if item["project_name"] == cfg.project_name),
                None,
            )

            if existing_index is not None:
                overwrite = prompt_bool(
                    f"已存在同名配置{cfg.project_name}，是否覆盖？",
                    default=True
                )
                if overwrite:
                    configs[existing_index] = asdict(cfg)
                    print(f"已覆盖配置：{cfg.project_name}")
                else:
                    print("已取消保存，返回菜单。")
                    continue
            else:
                configs.append(asdict(cfg))
                print(f"已创建配置：{cfg.project_name}")

            save_config_list(configs)
            return cfg

        elif choice == "3":
            delete_config(configs)

        elif choice == "4":
            raise SystemExit("用户已退出。")

        else:
            print("无效选择，请重新输入。")


#check root permission | 检查root权限
def ensure_root():
    if os.geteuid() != 0:
        raise SystemExit("请使用sudo或root运行此脚本。")


#这里往下是功能性函数了
#set up environment | 配置服务器环境
from pathlib import Path

def setup_environment(cfg: Config):
    print("\n一键环境配置")

    env_prefix = "DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a"
    run(f"{env_prefix} apt update")
    run(f"{env_prefix} apt upgrade -y")
    run(f"{env_prefix} apt install -y python3-venv python3-dev pkg-config build-essential libjpeg-dev zlib1g-dev libpng-dev nginx git certbot python3-certbot-nginx")

    if cfg.use_mysql:
        run(f"{env_prefix} apt install -y default-libmysqlclient-dev")

    Path(cfg.project_root).mkdir(parents=True, exist_ok=True)

    if not Path(cfg.venv_dir).exists():
        run(f"python3 -m venv {cfg.venv_dir}")

    run(f"{cfg.venv_dir}/bin/pip install --upgrade pip setuptools wheel")
    run(f"{cfg.venv_dir}/bin/pip install pymysql")

    Path(cfg.static_root).mkdir(parents=True, exist_ok=True)
    Path(cfg.media_root).mkdir(parents=True, exist_ok=True)

    pip_install = f"{cfg.venv_dir}/bin/pip install django gunicorn psycopg2-binary Pillow"
    if cfg.use_mysql:
        pip_install += " mysqlclient"

    run(pip_install)

    print("环境配置完成。")


#clone GitHub project | 拉取项目
def clone_project(cfg: Config):
    print("\nGitHub项目上传")

    if not cfg.git_url:
        raise RuntimeError("Git仓库地址不能为空。")

    repo_path = Path(cfg.repo_dir)
    git_dir = repo_path / ".git"

    if git_dir.exists():
        print("检测到已有git项目，执行拉取更新。")
        run("git fetch --all", cwd=cfg.repo_dir)
        run(f"git checkout {cfg.git_branch}", cwd=cfg.repo_dir)
        run(f"git pull origin {cfg.git_branch}", cwd=cfg.repo_dir)

    elif repo_path.exists() and any(repo_path.iterdir()):
        print("检测到目录已存在但不是git仓库，尝试初始化并拉取代码。")
        run("git init", cwd=cfg.repo_dir)
        run(f"git remote add origin {cfg.git_url}", cwd=cfg.repo_dir)
        run(f"git fetch origin {cfg.git_branch}", cwd=cfg.repo_dir)
        run(f"git checkout -b {cfg.git_branch} origin/{cfg.git_branch}", cwd=cfg.repo_dir)

    else:
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        run(f"git clone -b {cfg.git_branch} {cfg.git_url} {cfg.repo_dir}")

    req = repo_path / "requirements.txt"
    if req.exists():
        run(f"{cfg.venv_dir}/bin/pip install -r requirements.txt", cwd=cfg.repo_dir)

    print("项目拉取完成。")


#configure Gunicorn | 配置 Gunicorn
def configure_gunicorn(cfg: Config):
    print("\nGunicorn自动配置")
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
    print("\nNginx 自动配置")
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
    print("\nHTTPS自动配置")
    if not cfg.domain:
        raise RuntimeError("域名不能为空，HTTPS 需要域名。")
    if not prompt_bool("请确认域名已解析到本机且80/443端口已放行，继续申请证书吗", default=False):
        print("已跳过HTTPS配置。")
        return
    email_part = f"--email {cfg.email}" if cfg.email else "--register-unsafely-without-email"
    run(f"certbot --nginx {email_part} --agree-tos --no-eff-email -d {cfg.domain} -d www.{cfg.domain}")
    run("certbot renew --dry-run", check=False)
    print("HTTPS配置完成。")


#update project | 更新项目
def update_project(cfg: Config):
    print("\n更新项目")
    repo_path = Path(cfg.repo_dir)
    if not repo_path.exists():
        raise RuntimeError(f"项目目录不存在：{cfg.repo_dir}")

    if not (repo_path / ".git").exists():
        raise RuntimeError(f"{cfg.repo_dir} 不是一个Git仓库")

    branch = input(f"更新分支[{cfg.git_branch}]: ").strip() or cfg.git_branch
    cfg.git_branch = branch

    print(f"\n开始更新项目：{cfg.project_name}")
    print(f"目标分支：{branch}\n")

    py = f"{cfg.venv_dir}/bin/python"
    pip = f"{cfg.venv_dir}/bin/pip"

    run("git fetch origin", cwd=cfg.repo_dir)
    run(f"git checkout {branch}", cwd=cfg.repo_dir)
    run(f"git pull origin {branch}", cwd=cfg.repo_dir)
    run(f"git reset --hard origin/{branch}", cwd=cfg.repo_dir)

    req = repo_path / "requirements.txt"
    if req.exists():
        run(f"{pip} install -r requirements.txt", cwd=cfg.repo_dir)

    manage_py = repo_path / "manage.py"
    if manage_py.exists():
        run(
            f"bash -lc 'source {cfg.venv_dir}/bin/activate && {py} manage.py migrate'",
            cwd=cfg.repo_dir,
        )

        run(
            f"bash -lc 'source {cfg.venv_dir}/bin/activate && {py} manage.py collectstatic --noinput'",
            cwd=cfg.repo_dir,
        )

    else:
        print("未检测到manage.py，跳过migrate和collectstatic")

    run(f"sudo systemctl restart {cfg.service_name}")
    run("sudo systemctl reload nginx")

    print("项目更新完成。")


#quick update | 快速更新
def quick_update_project(cfg: Config):
    print("\n快速更新项目")

    repo_path = Path(cfg.repo_dir)

    if not repo_path.exists():
        raise RuntimeError(f"项目目录不存在：{cfg.repo_dir}")

    if not (repo_path / ".git").exists():
        raise RuntimeError(f"{cfg.repo_dir} 不是一个Git仓库")

    branch = cfg.git_branch
    print(f"\n开始快速更新项目：{cfg.project_name}")
    print(f"使用默认分支：{branch}\n")

    py = f"{cfg.venv_dir}/bin/python"
    pip = f"{cfg.venv_dir}/bin/pip"

    run("git fetch origin", cwd=cfg.repo_dir)
    run(f"git checkout {branch}", cwd=cfg.repo_dir)
    run(f"git pull origin {branch}", cwd=cfg.repo_dir)
    run(f"git reset --hard origin/{branch}", cwd=cfg.repo_dir)

    req = repo_path / "requirements.txt"
    if req.exists():
        run(f"{pip} install -r requirements.txt", cwd=cfg.repo_dir)

    manage_py = repo_path / "manage.py"
    if manage_py.exists():
        run(
            f"bash -lc 'source {cfg.venv_dir}/bin/activate && {py} manage.py migrate'",
            cwd=cfg.repo_dir,
        )
        run(
            f"bash -lc 'source {cfg.venv_dir}/bin/activate && {py} manage.py collectstatic --noinput'",
            cwd=cfg.repo_dir,
        )
    else:
        print("未检测到manage.py，跳过migrate和collectstatic")

    run(f"sudo systemctl restart {cfg.service_name}")
    run("sudo systemctl reload nginx")

    print("快速更新完成。")


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


#start website | 启动网站
def start_website(cfg: Config):
    print("\n启动网站服务")
    run(f"systemctl daemon-reload", check=False)
    print("启动 Gunicorn 服务...")
    run(f"systemctl restart {cfg.service_name}")
    print("启动 Nginx...")
    run("systemctl restart nginx")
    print("网站服务已启动.")
    print("\n服务状态：")
    run(f"systemctl status {cfg.service_name} --no-pager", check=False)
    run("systemctl status nginx --no-pager", check=False)


#stop website | 停止网站
def stop_website(cfg: Config):
    print("\n[12] 停止网站")

    run(f"systemctl stop {cfg.service_name}", check=False)
    run("systemctl stop nginx", check=False)

    print("网站已停止")

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
        "8": lambda: update_project(cfg),
        "9": lambda: quick_update_project(cfg),
        "10": lambda: start_website(cfg),
        "11": lambda: stop_website(cfg),
    }
    while True:
        show_summary(cfg)
        print("请选择操作:")
        print("1) 配置环境")
        print("2) GitHub项目拉取")
        print("3) Gunicorn自动配置")
        print("4) Nginx自动配置")
        print("5) HTTPS自动配置 #暂时有故障")
        print("6) 数据库迁移和收集静态文件")
        print("7) 全部执行 1 → 6")
        print("8) 选择分支进行更新")
        print("9) 快速更新")
        print("10) 启动网站")
        print("11) 关闭网站")
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
