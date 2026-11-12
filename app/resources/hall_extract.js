(function () {
    const clean = (value) => String(value == null ? '' : value)
        .replace(/\s+/g, ' ').trim();
    const result = {
        ok: false,
        url: location.href,
        title: document.title,
        total: 0,
        list: [],
        stat: null,
        notice: ''
    };

    try {
        const noticeNode = document.querySelector(
            '.service-appeal .tips, .nodata h3, .nogoods h3'
        );
        if (noticeNode) { result.notice = clean(noticeNode.innerText); }
    } catch (err) {}

    try {
        let vm = null;
        const walk = (node, depth) => {
            if (!node || depth > 24) { return null; }
            if (Array.isArray(node.hallList)) { return node; }
            const children = node.$children || [];
            for (let i = 0; i < children.length; i += 1) {
                const hit = walk(children[i], depth + 1);
                if (hit) { return hit; }
            }
            return null;
        };
        const rootEl = document.querySelector('#app');
        if (rootEl && rootEl.__vue__) { vm = walk(rootEl.__vue__, 0); }
        if (!vm) {
            let el = document.querySelector('.main-order-wrap')
                || document.querySelector('.recycle-hall-list');
            while (el && !vm) {
                if (el.__vue__) { vm = walk(el.__vue__, 0); }
                el = el.parentElement;
            }
        }
        if (vm) {
            result.ok = true;
            result.total = Number(vm.totalRecord || vm.hallList.length || 0);
            const hallData = vm.hallData || null;
            if (hallData) {
                result.stat = {
                    dayCount: hallData.quoteCntDay,
                    dayAvg: hallData.quoteAvgTimeDay,
                    monthCount: hallData.quoteCntMonth,
                    monthAvg: hallData.quoteAvgTimeMonth,
                    currMonthCount: hallData.currMonthCnt,
                    currMonthMoney: hallData.currMonthMoney,
                    agreed: hallData.sellerAgreeQuoteCnt
                };
            }
            result.list = vm.hallList.map((item) => ({
                title: item.title || item.goodtitle || '',
                attrs: item.subTitlePc || '',
                quotePerson: item.quotePerson,
                online: item.onLineShow,
                myQuote: (item.showMyQuotePrice && item.showMyQuotePrice > 0)
                    ? item.myQuotePrice : '',
                remark: item.recycleRemark || '',
                goodsId: item.goodsId,
                status: item.quoteStatus
            }));
            return JSON.stringify(result);
        }
    } catch (err) { result.error = String(err); }

    try {
        const nodes = Array.from(
            document.querySelectorAll('.recycle-hall-list .order-item')
        );
        result.list = nodes.map((el) => {
            const attrs = Array.from(
                el.querySelectorAll('.attr-box .attr-item')
            ).map((node) => clean(node.innerText)).join('|');
            return {
                title: clean((el.querySelector('.goods-title h3') || {}).innerText),
                attrs: attrs,
                quotePerson: '',
                online: clean((el.querySelector('.group-info') || {}).innerText),
                myQuote: clean((el.querySelector('.order-price-box h3') || {}).innerText),
                remark: '',
                goodsId: ''
            };
        });
        result.total = result.list.length;
        result.ok = result.list.length > 0;
    } catch (err) { result.error = String(err); }
    return JSON.stringify(result);
})();
