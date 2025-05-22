1. 我需要通过python技术栈来实现每分钟获取一次这个url
https://bscscan.com/address/0xd3fbaa9baec8620dcfc9d76c71efdfce4c544e19
2. 这个URL为IDO的地址，需要获取这个地址募集的BNB数量
3. 提供配置文件，配置文件中需要配置获取的URL，以及获取的频率
4. 从这个模式中匹配关键词提取数量
```
<div>
                        <h4 class="text-cap mb-1">BNB Balance
                            </h4>
                        <div>
                            <div class='d-flex'>
                                <img class='me-1' width='15' data-img-theme='light' src='/assets/bsc/images/svg/logos/token-light.svg?v=25.5.3.3' alt='BNB Smart Chain Logo'>
                                <img class='me-1' width='15' data-img-theme='dim' src='/assets/bsc/images/svg/logos/token-dim.svg?v=25.5.3.3' alt='BNB Smart Chain Logo'>
                                <img class='me-1' width='15' data-img-theme='dark' src='/assets/bsc/images/svg/logos/token-dark.svg?v=25.5.3.3' alt='BNB Smart Chain Logo'>
                                3,341<b>.</b>
                                513205067415012159 BNB
                            </div>
                        </div>
                    </div>
```

## BNB Balance Monitor

### 使用说明

1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 配置：
   在 `config.json` 文件中设置：
   - `url`: 要监控的BNB地址URL
   - `frequency_seconds`: 监控频率（秒）
   - `log_file`: 日志文件名

3. 运行脚本：
   ```
   python bnb_monitor.py
   ```

4. 监控结果将输出到控制台和指定的日志文件中
