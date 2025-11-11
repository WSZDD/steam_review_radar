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
});