/* 使用 jQuery 的 $(document).ready() 来确保所有 HTML 元素都已加载
  这一个函数会包裹我们所有的 JS 功能
*/
$(document).ready(function(){
    var wordcloudChart = null; // 用于高亮联动
    var wordCloudData = [];     // 存储词云的原始数据
    // (我们不再需要 originalWordCloudColorFunc，因为 'downplay' 会正确重置)

    // ===================================
    // 1. 评论卡片点击弹窗 (无变化)
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
    // 2. 表单提交 "加载中" 提示 (无变化)
    // ===================================
    $("form").on("submit", function() {
        $("#loadingOverlay").css("display", "flex");
    });

    // ===================================
    // 3. ECharts 交互式词云 (封装到函数)
    // ===================================
    function initWordCloud() {
        const chartDom = document.getElementById('wordcloud_chart');
        // 检查是否已初始化，防止重复加载
        if (!chartDom || chartDom.dataset.initialized) return;
        chartDom.dataset.initialized = 'true';

        console.log("Lazy Loading: initWordCloud");

        wordCloudData = JSON.parse(chartDom.dataset.wordData);
        const topicMap = JSON.parse(chartDom.dataset.topicMap);

        if (wordCloudData && wordCloudData.length > 0) {
            wordCloudChart = echarts.init(chartDom); // 赋值给全局变量

            const option = {
                tooltip: { 
                    trigger: 'item',
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    borderColor: '#66c0f4',
                    borderWidth: 1,
                    textStyle: { color: '#fff' },
                    // 【已应用】限制弹窗宽度
                    extraCssText: 'max-width: 350px; white-space: normal; word-break: break-word;', 
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
                    emphasis: { 
                        textStyle: {
                            color: '#FFFFFF', 
                            shadowBlur: 50,
                            shadowColor: '#4fc3f7'
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

    // ===================================
    // 4. 时序图 (封装到函数)
    // ===================================
    function initTimeSeriesChart() {
        const timeChartDom = document.getElementById('time_series_chart');
        if (!timeChartDom || timeChartDom.dataset.initialized) return;
        timeChartDom.dataset.initialized = 'true';

        console.log("Lazy Loading: initTimeSeriesChart");

        const timeData = JSON.parse(timeChartDom.dataset.timeSeries);

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
                legend: {
                    data: ['好评数', '差评数'],
                    textStyle: { color: '#e0e0e0' }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '10%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: timeData.dates,
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
                series: [
                    {
                        name: '好评数',
                        type: 'line',
                        smooth: true,
                        data: timeData.positive_counts,
                        itemStyle: { color: '#4CAF50' },
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
                        data: timeData.negative_counts,
                        itemStyle: { color: '#F44336' },
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

    // ===================================
    // 5. 游玩时长情感图 (封装到函数)
    // ===================================
    function initPlaytimeSentimentChart() {
        const Sentimenttime = document.getElementById('playtime_sentiment_chart');
        if (!Sentimenttime || Sentimenttime.dataset.initialized) return;
        Sentimenttime.dataset.initialized = 'true';

        console.log("Lazy Loading: initPlaytimeSentimentChart");

        const timeData = JSON.parse(Sentimenttime.dataset.playtimeSentiment); 

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
                    data: timeData.labels,
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
                        type: 'bar',
                        smooth: true,
                        data: timeData.positive_scores,
                        itemStyle: { color: '#4CAF50' },
                    },
                    {
                        name: '差评情感',
                        type: 'bar',
                        smooth: true,
                        data: timeData.negative_scores,
                        itemStyle: { color: '#F44336' },
                    }
                ]
            };
            timeChart.setOption(option);
            $(window).on('resize', function () {
                timeChart.resize();
            });
        }
    }

    // ===================================
    // 6. 雷达图 (封装到函数)
    // ===================================
    function initRadarChart() {
        const radarDom = document.getElementById('radarChart');
        if (!radarDom || radarDom.dataset.initialized) return;
        radarDom.dataset.initialized = 'true';

        console.log("Lazy Loading: initRadarChart");

        try {
            const radarData = JSON.parse(radarDom.dataset.radar);

            if (radarData && radarData.indicator && radarData.value) {
                const radarChart = echarts.init(radarDom);
                const radarOption = {
                    tooltip: {
                        trigger: 'item'
                    },
                    radar: {
                        shape: 'circle', 
                        indicator: radarData.indicator,
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
                                    value: radarData.value,
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
                
                $(window).on('resize', function () {
                    radarChart.resize();
                });
            }
        } catch (e) {
            console.error("雷达图 ECharts 渲染失败:", e);
        }
    }


    // ===================================
    // 7. 词云图交互 (无变化)
    // ===================================
    
    // 7.A. 点击主题列表
    $(document).on("click", ".topic-item", function(){
        if (!wordCloudChart || wordCloudData.length === 0) return; 
        
        const topicId = $(this).data("topic-id"); 

        let highlightIndices = [];
        let downplayIndices = [];
        wordCloudData.forEach((item, index) => {
            if (item.topic_id === topicId) {
                highlightIndices.push(index);
            } else {
                downplayIndices.push(index);
            }
        });

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

        $("#resetWordcloudHighlight").show();
    });

    // 7.B. 点击“重置高亮”按钮 (使用 'downplay' 修复)
    $(document).on("click", "#resetWordcloudHighlight", function(e){
        e.preventDefault(); 
        if (!wordCloudChart) return;

        // 【已应用】使用 'downplay' 动作来取消所有高亮和淡化
        wordCloudChart.dispatchAction({
            type: 'downplay',
            seriesIndex: 0,
            dataIndex: wordCloudData.map((_, index) => index)
        });
        
        $(this).hide();
    });


    // --- 【核心修改】 ---
    // ===================================
    // 8. Intersection Observer 懒加载
    // ===================================

    // 检查浏览器是否支持 IntersectionObserver
    if ('IntersectionObserver' in window) {
        
        // 映射图表 ID 到它们的初始化函数 (无变化)
        const chartInitMap = {
            'wordcloud_chart': initWordCloud,
            'time_series_chart': initTimeSeriesChart,
            'playtime_sentiment_chart': initPlaytimeSentimentChart,
            'radarChart': initRadarChart
        };

        // --- 【关键修改】更新回调函数 ---
        const lazyLoadCallback = (entries, observer) => {
            entries.forEach(entry => {
                // 检查元素是否进入视口
                if (entry.isIntersecting) {
                    const target = entry.target; // 这是 .observe-fade-in 元素
                    target.classList.add('is-visible');

                    let chartElement = null;
                    const chartId = target.id;

                    if (chartInitMap[chartId]) {
                        chartElement = target;
                    } else {
                        chartElement = target.querySelector('#wordcloud_chart, #time_series_chart, #playtime_sentiment_chart, #radarChart');
                    }

                    if (chartElement) {
                        const idToInit = chartElement.id;
                        const initFunction = chartInitMap[idToInit];
                        
                        // 检查图表元素是否已初始化
                        if (initFunction && !chartElement.dataset.initialized) {
                            initFunction(); 
                            // (initFunction 内部会设置 .dataset.initialized)
                        }
                    }
                    
                    observer.unobserve(target);
                }
            });
        };

        const lazyLoadObserver = new IntersectionObserver(lazyLoadCallback, {
            root: null, // 相对于浏览器视口
            threshold: 0.1  // 元素进入视口 10% 时触发
        });

        document.querySelectorAll('.observe-fade-in').forEach(element => {
            if (element) {
                lazyLoadObserver.observe(element);
            }
        });

    } else {
        // 如果浏览器太旧不支持 (无变化)
        console.warn("IntersectionObserver not supported. Loading all charts immediately.");
        initWordCloud();
        initTimeSeriesChart();
        initPlaytimeSentimentChart();
        initRadarChart();
        document.querySelectorAll('.observe-fade-in').forEach(element => {
            element.classList.add('is-visible');
        });
    }
    
    if (typeof tsParticles !== 'undefined') {
        console.log("tsParticles is available.");
        tsParticles.load("tsparticles", {
            // "fullScreen": false, // 我们用 CSS 手动控制
            "interactivity": {
                "events": {
                    "onHover": { // 鼠标悬停
                        "enable": true,
                        "mode": "grab" // 模式：抓取
                    },
                    "onClick": { // 鼠标点击
                        "enable": true,
                        "mode": "push" // 模式：推送
                    }
                },
                "modes": {
                    "grab": {
                        "distance": 150, 
                        "links": { "opacity": 0.8 }
                    },
                    "push": {
                        "quantity": 2 
                    }
                }
            },
            "particles": {
                "color": { "value": "#ffffff" },
                "links": { // 粒子连线
                    "color": { "value": "#66c0f4" }, // 连线颜色：Steam 蓝色
                    "distance": 150,
                    "enable": true,
                    "opacity": 0.3,
                    "width": 1
                },
                "move": { // 粒子移动
                    "enable": true,
                    "speed": 1.5,
                    "direction": "none",
                    "random": true, // 确保这里是 'true',
                    "straight": false,
                    "outModes": "out"
                },
                "number": { // 粒子数量
                    "value": 60,
                    "density": {
                        "enable": true,
                        "area": 800
                    }
                },
                "opacity": { "value": 0.4 },
                "shape": { "type": "circle" },
                "size": { "value": { "min": 1, "max": 3 } }
            },
            "detectRetina": true
        });
    }
});