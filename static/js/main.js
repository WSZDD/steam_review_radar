/* 使用 jQuery 的 $(document).ready() 来确保所有 HTML 元素都已加载
  这一个函数会包裹我们所有的 JS 功能
*/
$(document).ready(function(){

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
        // 避免重复添加
        if ($("#loading").length === 0) {
            $("body").append('<div id="loading" class="text-center mt-4">⏳ 加载中，请稍候...</div>');
        }
    });

    // ===================================
    // 3. ECharts 交互式词云 (来自我们之前的逻辑)
    // ===================================
    
    // 3.1 查找 ECharts 容器
    const chartDom = document.getElementById('wordcloud_chart');
    
    // 3.2 检查容器是否存在 (如果页面上没有词云，就不执行)
    if (chartDom) {
        
        // 3.3 从 HTML 的 'data-*' 属性中读取数据
        const wordData = JSON.parse(chartDom.dataset.wordData);
        const topicMap = JSON.parse(chartDom.dataset.topicMap);

        // 3.4 仅当有数据时才初始化图表
        if (wordData && wordData.length > 0) {
            
            const myChart = echarts.init(chartDom);
            const option = {
                tooltip: {
                    trigger: 'item',
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    borderColor: '#66c0f4',
                    borderWidth: 1,
                    textStyle: { color: '#fff' },
                    confine: true, 
                    extraCssText: 'width: 300px; white-space: normal; word-wrap: break-word;',
                    formatter: function (params) {
                        const word = params.data.name;
                        const topic_id = params.data.topic_id;
                        const topic_info = topicMap[topic_id]; 
                        if (topic_info) {
                            return `<strong style="font-size: 1.1em;">${word}</strong><br/>` +
                                   `<strong style="color: #66c0f4;">主题:</strong> ${topic_info.keywords}<br/>` +
                                   `<strong style="color: #66c0f4;">摘要:</strong> ${topic_info.summary}`;
                        } else {
                            return `<strong>${word}</strong><br/> (无关联主题)`;
                        }
                    }
                },
                series: [{
                    type: 'wordCloud',
                    shape: 'pentagon',
                    data: wordData,
                    sizeRange: [14, 60],
                    rotationRange: [-45, 45],
                    rotationStep: 15,
                    gridSize: 10,
                    drawOutOfBound: false,
                    textStyle: {
                        color: function () {
                            return 'rgb(' + [
                                Math.round(Math.random() * 160) + 95,
                                Math.round(Math.random() * 160) + 95,
                                Math.round(Math.random() * 160) + 95
                            ].join(',') + ')';
                        }
                    },
                    emphasis: {
                        textStyle: {
                            shadowBlur: 10,
                            shadowColor: '#333'
                        }
                    }
                }]
            }; // option 结束

            myChart.setOption(option);
            
            // 3.5 窗口大小调整 (使用 jQuery)
            $(window).on('resize', function () {
                myChart.resize();
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
});