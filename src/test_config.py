#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置模块测试脚本
用于测试配置加载和合并功能
"""

import os
import sys
import json
import time
from datetime import datetime
from logging_config import setup_logging
import logging
import tempfile

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def test_config_loading():
    """测试配置加载"""
    try:
        # 导入配置模块
        from config import config, load_config, merge_configs
        
        # 打印当前配置
        logger.info("当前配置:")
        for section, settings in config.items():
            logger.info(f"  - {section}:")
            for key, value in settings.items():
                logger.info(f"    - {key}: {value}")
        
        # 测试配置合并
        logger.info("测试配置合并")
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
            # 写入测试配置
            test_config = {
                "github": {
                    "per_page": 50,
                    "max_repos": 100
                },
                "ai": {
                    "model": "test-model",
                    "temperature": 0.2
                },
                "new_section": {
                    "test_key": "test_value"
                }
            }
            
            json.dump(test_config, temp_file)
            temp_file_path = temp_file.name
        
        # 加载测试配置
        logger.info(f"从临时文件加载配置: {temp_file_path}")
        test_loaded_config = load_config(temp_file_path)
        
        # 打印加载的配置
        logger.info("加载的测试配置:")
        for section, settings in test_loaded_config.items():
            logger.info(f"  - {section}:")
            for key, value in settings.items():
                logger.info(f"    - {key}: {value}")
        
        # 合并配置
        logger.info("合并默认配置和测试配置")
        from config import DEFAULT_CONFIG
        merged_config = merge_configs(DEFAULT_CONFIG, test_loaded_config)
        
        # 打印合并后的配置
        logger.info("合并后的配置:")
        for section, settings in merged_config.items():
            logger.info(f"  - {section}:")
            for key, value in settings.items():
                logger.info(f"    - {key}: {value}")
        
        # 验证合并结果
        assert merged_config["github"]["per_page"] == 50, "配置合并失败: github.per_page 应为 50"
        assert merged_config["ai"]["model"] == "test-model", "配置合并失败: ai.model 应为 test-model"
        assert "new_section" in merged_config, "配置合并失败: 新部分应该存在"
        assert merged_config["new_section"]["test_key"] == "test_value", "配置合并失败: 新键值应该存在"
        
        # 清理临时文件
        os.unlink(temp_file_path)
        logger.info("清理临时文件")
        
        return True
    except Exception as e:
        logger.error(f"测试配置加载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("开始测试配置模块")
    
    # 测试配置加载
    if not test_config_loading():
        logger.error("配置模块测试失败")
        return
    
    logger.info("配置模块测试完成")

if __name__ == "__main__":
    main()