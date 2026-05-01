# 初始化目录
if [ ! -d "assets" ]; then
  mkdir -p "assets"
fi

# 安装Python三方包依赖
pip install -r requirements.txt
