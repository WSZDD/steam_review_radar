/* 使用 jQuery 的 $(document).ready() 来确保所有 HTML 元素都已加载
  这一个函数会包裹我们所有的 JS 功能
*/
$(document).ready(function(){
    var wordcloudChart = null; // 用于高亮联动
    var wordCloudData = [];     // 存储词云的原始数据
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
        // --- 【修改】读取所有 data-* 属性 ---
        var steamid = $(this).data("steamid");
        var appid = $(this).data("appid");
        var content_full = $(this).data("content");
        var playtime = $(this).data("playtime"); // 新增
        var votes = $(this).data("votes");       // 新增
        var votedUpStr = $(this).data("voted-up").toString(); // 新增 (转为字符串)
        
        console.log("请求 URL:", `/comment_detail/${steamid}/${appid}`);

        // AJAX 调用后端接口获取昵称和头像
        $.getJSON(`/comment_detail/${steamid}/${appid}`, function(data){
            // 填充已有内容
            $("#modalAuthor").text(data.nickname);
            $("#modalAvatar").attr("src", data.avatar);
            $("#modalContent").text(content_full);

            // --- 【新增】填充统计数据 ---
            
            // 1. 格式化并设置时长和获赞
            var playtimeHours = (playtime / 60).toFixed(1);
            $("#modalPlaytime").text(playtimeHours + " 小时");
            $("#modalVotes").text(votes);

            // 2. 设置好评/差评徽章
            var $badge = $("#modalReviewType");
            // 检查 'True' (来自 Jinja) 或 true (来自 JS)
            console.log("voted_up 字符串值:", votedUpStr);
            if (votedUpStr.toLowerCase() === '1') { 
                $badge.text("👍好评").removeClass("bg-danger").addClass("bg-primary");
            } else {
                $badge.text("👎差评").removeClass("bg-primary").addClass("bg-danger");
            }
            // --- 新增结束 ---

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
        
        // --- 【修改】将数据赋给全局变量 ---
        wordCloudData = JSON.parse(chartDom.dataset.wordData);
        const topicMap = JSON.parse(chartDom.dataset.topicMap);
        // --- 【修改结束】 ---

        if (wordCloudData && wordCloudData.length > 0) {
            
            // --- 【修改】将 ECharts 实例赋给全局变量 ---
            wordCloudChart = echarts.init(chartDom);
            // --- 【修改结束】 ---

            const option = {
                tooltip: { /* (保留 tooltip 逻辑) */
                    trigger: 'item',
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    borderColor: '#66c0f4',
                    borderWidth: 1,
                    textStyle: { color: '#fff' },
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
                series: [{ /* (保留 series 逻辑) */
                    type: 'wordCloud',
                    shape: 'pentagon',
                    data: wordCloudData,
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
                    emphasis: { // <-- 【重要】高亮时的样式
                        textStyle: {
                            color: '#FFFFFF', // 高亮时变白色
                            shadowBlur: 50,
                            shadowColor: '#4fc3f7' // 蓝色辉光
                        }
                    }
                }]
            }; 
            wordCloudChart.setOption(option);
            
            $(window).on('resize', function () {
                wordCloudChart.resize();
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

    $(document).on("click", ".topic-item", function(){
        if (!wordCloudChart || wordCloudData.length === 0) return; // 检查图表是否已初始化
        
        const topicId = $(this).data("topic-id"); 

        // 1. 找到所有匹配和不匹配的词的 *索引*
        let highlightIndices = [];
        let downplayIndices = [];
        wordCloudData.forEach((item, index) => {
            // BERTopic 的 topic_id 是数字，jQuery data() 也会返回数字
            if (item.topic_id === topicId) {
                highlightIndices.push(index);
            } else {
                downplayIndices.push(index);
            }
        });

        // 2. 调度 ECharts 动作 (这 *不会* 重新布局)
        wordCloudChart.dispatchAction({
            type: 'downplay',
            seriesIndex: 0,
            dataIndex: downplayIndices
        });
        wordCloudChart.dispatchAction({
            type: 'highlight',
            seriesIndex: 0,
            dataIndex: highlightIndices
        });

        // 3. 显示“重置”按钮
        $("#resetWordcloudHighlight").show();
    });

    // 7.B. 点击“重置高亮”按钮
    $(document).on("click", "#resetWordcloudHighlight", function(e){
        e.preventDefault(); // 阻止 <a> 标签跳转
        if (!wordCloudChart) return;

        // 重新高亮所有数据
        wordCloudChart.dispatchAction({
            type: 'highlight',
            seriesIndex: 0,
            dataIndex: wordCloudData.map((_, index) => index)
        });
        
        // 隐藏自己
        $(this).hide();
    });
});