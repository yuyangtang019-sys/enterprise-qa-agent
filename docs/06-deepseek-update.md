# DeepSeek变更记录

用户从最初无配置情况下的离线工程验证，改为明确要求真实DeepSeek-V4.1-Flash-1017。用户已自行运行configure_deepseek.py配置本地.env.local，程序获授权加载并调用真实端点，不能再称“缺密钥、真实未验证”。

官方deepseek-flash服务别名访问该系列，trace记录指定名称、API名称和服务返回名称。CLI与HTTP业务验收均为真实调用；旧Mock仅历史记录。真实结果见examples/real、examples/http，修复记录见bugs-and-fixes.md。

配置只加载三个允许项，环境优先，无shell求值；密钥不回显、不入trace/源码。默认loopback HTTP，客户端不能指定端点或路径。Git忽略.env.local，最终安全等值扫描不输出密钥。
