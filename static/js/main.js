/* 使用 jQuery 的 $(document).ready() 来确保所有 HTML 元素都已加载
  这一个函数会包裹我们所有的 JS 功能
*/
$(document).ready(function(){
    var wordcloudChart = null; // 用于高亮联动
    var globalWordData = [];     // 存储词云的原始数据
    var originalWordCloudColorFunc = function () { // 存储原始颜色
        return 'rgb(' + [
            Math.round(Math.random() * 160) + 95,
            Math.round(Math.random() * 160) + 95,
            Math.round(Math.random() * 160) + 95
        ].join(',') + ')';
    };
    // ===================================
    // 1. 评论卡片点击弹窗 (来自你的 jQuery)
    // ===================================
    $(document).on("click", ".comment-card", function(){
        var steamid = $(this).data("steamid");
        var appid = $(this).data("appid");
        var content_full = $(this).data("content");
        
        console.log("请求 URL:", `/comment_detail/${steamid}/${appid}`);

        // AJAX 调用后端接口获取昵称和头像
        $.getJSON(`/comment_detail/${steamid}/${appid}`, function(data){
            $("#modalAuthor").text(data.nickname);
            $("#modalAvatar").attr("src", data.avatar);
            $("#modalContent").text(content_full);

            // 使用 Bootstrap 5 API 显示 Modal
            var myModal = new bootstrap.Modal(document.getElementById('commentModal'));
            myModal.show();
        });
    });

    // ===================================
    // 2. 表单提交 "加载中" 提示 (来自你的 jQuery)
    // ===================================
    $("form").on("submit", function() {
        $("#loadingOverlay").css("display", "flex");
    });

    // ===================================
    // 3. ECharts 交互式词云 (来自我们之前的逻辑)
    // ===================================
    
    // 3.1 查找 ECharts 容器
    const chartDom = document.getElementById('wordcloud_chart');
    if (chartDom) {
        // 3.3 从 HTML 的 'data-*' 属性中读取数据
        globalWordData = JSON.parse(chartDom.dataset.wordData); // <-- 【修改】 存储到全局
        const topicMap = JSON.parse(chartDom.dataset.topicMap);

        // 3.4 仅当有数据时才初始化图表
        if (globalWordData && globalWordData.length > 0) { // <-- 【修改】
            
            wordcloudChart = echarts.init(chartDom); // <-- 【修改】 存到全局
            const option = {
                // ... (tooltip 保持不变, 确保包含 turn 23 的换行修复) ...
                series: [{
                    type: 'wordCloud',
                    data: globalWordData, // <-- 【修改】
                    // ...
                    textStyle: {
                        color: originalWordCloudColorFunc // <-- 【修改】
                    },
                    // ...
                }]
            }; // option 结束

            wordcloudChart.setOption(option); // <-- 【修改】
            
            // 3.5 窗口大小调整 (使用 jQuery)
            $(window).on('resize', function () {
                wordcloudChart.resize(); // <-- 【修改】
            });
        }
    }

    // --- 【核心修改】替换这个时序图逻辑 ---
    const timeChartDom = document.getElementById('time_series_chart');
    if (timeChartDom) {
        const timeData = JSON.parse(timeChartDom.dataset.timeSeries);

        // 检查新数据结构是否有效
        if (timeData && timeData.dates && timeData.dates.length > 0) {
            const timeChart = echarts.init(timeChartDom);
            const option = {
                tooltip: {
                    trigger: 'axis',
                    formatter: function (params) {
                        let tooltip = `<strong>${params[0].name}</strong><br/>`;
                        params.forEach(item => {
                            tooltip += `${item.marker} ${item.seriesName}: ${item.value}<br/>`;
                        });
                        return tooltip;
                    },
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    borderColor: '#66c0f4',
                    textStyle: { color: '#fff' }
                },
                legend: { // <-- 新增图例
                    data: ['好评数', '差评数'],
                    textStyle: { color: '#e0e0e0' }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '10%', // 增加底部空间给 dataZoom
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: timeData.dates, // X 轴 (日期)
                    axisLine: { lineStyle: { color: '#8392A5' } }
                },
                yAxis: {
                    type: 'value',
                    name: '评论数',
                    axisLine: { lineStyle: { color: '#8392A5' } },
                    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
                },
                dataZoom: [
                    { type: 'inside', start: 0, end: 100 },
                    { start: 0, end: 100 }
                ],
                series: [ // <-- 【核心修改】两条线
                    {
                        name: '好评数',
                        type: 'line',
                        smooth: true,
                        data: timeData.positive_counts, // Y 轴 (好评)
                        itemStyle: { color: '#4CAF50' }, // 绿色
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: 'rgba(76, 175, 80, 0.5)'
                            }, {
                                offset: 1,
                                color: 'rgba(76, 175, 80, 0.0)'
                            }])
                        }
                    },
                    {
                        name: '差评数',
                        type: 'line',
                        smooth: true,
                        data: timeData.negative_counts, // Y 轴 (差评)
                        itemStyle: { color: '#F44336' }, // 红色
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                                offset: 0,
                                color: 'rgba(244, 67, 54, 0.5)'
                            }, {
                                offset: 1,
                                color: 'rgba(244, 67, 54, 0.0)'
                            }])
                        }
                    }
                ]
            };
            timeChart.setOption(option);
            $(window).on('resize', function () {
                timeChart.resize();
            });
        }
    }

    const Sentimenttime = document.getElementById('playtime_sentiment_chart'); // <-- 使用新 ID
    if (Sentimenttime) {
        const timeData = JSON.parse(Sentimenttime.dataset.playtimeSentiment); // <-- 使用新 data- 

        // 检查新数据结构是否有效
        if (timeData && timeData.labels && timeData.labels.length > 0) {
            const timeChart = echarts.init(Sentimenttime);
            const option = {
                tooltip: {
                    trigger: 'axis',
                    formatter: function (params) {
                        let tooltip = `<strong>${params[0].name}</strong><br/>`;
                        params.forEach(item => {
                            tooltip += `${item.marker} ${item.seriesName}: ${item.value.toFixed(1)}分<br/>`;
                        });
                        return tooltip;
                    },
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    borderColor: '#66c0f4',
                    textStyle: { color: '#fff' }
                },
                legend: {
                    data: ['好评情感', '差评情感'],
                    textStyle: { color: '#e0e0e0' }
                },
                grid: {
                    left: '3%', right: '4%', bottom: '3%', containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: timeData.labels, // X 轴 (时长标签)
                    axisLine: { lineStyle: { color: '#8392A5' } }
                },
                yAxis: {
                    type: 'value',
                    name: '平均情感分 (0-100)',
                    min: 0,
                    max: 100,
                    axisLine: { lineStyle: { color: '#8392A5' } },
                    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
                },
                series: [
                    {
                        name: '好评情感',
                        type: 'bar', // 使用柱状图
                        smooth: true,
                        data: timeData.positive_scores, // Y 轴 (好评均分)
                        itemStyle: { color: '#4CAF50' }, // 绿色
                    },
                    {
                        name: '差评情感',
                        type: 'bar', // 使用柱状图
                        smooth: true,
                        data: timeData.negative_scores, // Y 轴 (差评均分)
                        itemStyle: { color: '#F44336' }, // 红色
                    }
                ]
            };
            timeChart.setOption(option);
            $(window).on('resize', function () {
                timeChart.resize();
            });
        }
    }

    const radarDom = document.getElementById('radarChart');
    if (radarDom) {
        try {
            // 假设你在 index.html 中是这样传递数据的:
            // <div id="radarChart" data-radar="{{ radar_json | safe }}"></div>
            const radarData = JSON.parse(radarDom.dataset.radar);

            // 检查数据是否有效
            if (radarData && radarData.indicator && radarData.value) {
                const radarChart = echarts.init(radarDom);
                const radarOption = {
                    tooltip: {
                        trigger: 'item'
                    },
                    radar: {
                        shape: 'circle', 
                        indicator: radarData.indicator, // 使用后端传来的维度定义
                        axisName: {
                            color: '#ccc',
                            fontSize: 12
                        },
                        splitArea: {
                            areaStyle: {
                                color: ['rgba(50, 50, 50, 0.2)', 'rgba(40, 40, 40, 0.2)'],
                                shadowColor: 'rgba(0, 0, 0, 0.2)',
                                shadowBlur: 10
                            }
                        },
                        splitLine: {
                            lineStyle: {
                                color: 'rgba(100, 100, 100, 0.5)'
                            }
                        }
                    },
                    series: [
                        {
                            name: '游戏维度分析',
                            type: 'radar',
                            data: [
                                {
                                    value: radarData.value, // 使用后端计算的平均分
                                    name: '游戏维度分析',
                                    areaStyle: {
                                        color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.5, [
                                            { offset: 0, color: 'rgba(0, 255, 255, 0.5)' },
                                            { offset: 1, color: 'rgba(0, 128, 128, 0.2)' }
                                        ])
                                    },
                                    lineStyle: {
                                        color: 'rgba(0, 255, 255, 0.8)'
                                    },
                                    itemStyle: {
                                        color: 'rgba(0, 255, 255, 1)'
                                    }
                                }
                            ]
                        }
                    ]
                };
                radarChart.setOption(radarOption);
                
                // 响应式调整
                $(window).on('resize', function () {
                    radarChart.resize();
                });
            }
        } catch (e) {
            console.error("雷达图 ECharts 渲染失败:", e);
        }
    }

    $('.dashboard-block').on('click', '.topic-item', function() {
        if (!wordcloudChart || !globalWordData) return;

        // 从 HTML data- 属性获取 topic_id
        const clickedTopicId = $(this).data('topic-id');
        
        // 1. 显示重置按钮
        $('#resetWordcloudHighlight').show();
        
        // 2. 更新词云
        // 我们通过 setOption 动态修改 *每一个* 词的 textStyle
        wordcloudChart.setOption({
            series: [{
                // ECharts 会智能合并, 我们只提供 data
                data: globalWordData.map(word => {
                    // 必须返回一个包含所有原始属性的新对象
                    return {
                        name: word.name,
                        value: word.value,
                        topic_id: word.topic_id,
                        // 【核心】: 动态设置颜色
                        textStyle: {
                            // 匹配主题的词：高亮 (蓝色)
                            // 不匹配的词： 变灰 (半透明)
                            color: (word.topic_id == clickedTopicId) 
                                   ? '#4fc3f7' 
                                   : 'rgba(200, 200, 200, 0.3)'
                        }
                    };
                })
            }]
        });
    });

    // 监听词云重置按钮
    $('#resetWordcloudHighlight').on('click', function() {
        if (!wordcloudChart || !globalWordData) return;
        
        // 1. 隐藏按钮
        $(this).hide();
        
        // 2. 恢复词云
        wordcloudChart.setOption({
            series: [{
                data: globalWordData, // 传回原始数据
                textStyle: {
                    // 传回原始的随机颜色函数
                    color: originalWordCloudColorFunc
                }
            }]
        });
    });
});