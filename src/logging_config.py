import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """设置日志配置
    
    Args:
        log_level: 日志级别，默认为INFO
    """
    # 创建logs目录（如果不存在）
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 设置日志文件名，包含日期
    log_file = os.path.join(logs_dir, f"star_manager_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # 文件处理器
            logging.FileHandler(log_file, encoding='utf-8'),
            # 控制台处理器
            logging.StreamHandler()
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger('github').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logging.info(f"日志已配置，日志文件: {log_file}")
    
    return logging.getLogger(__name__)