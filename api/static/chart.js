(() => {
    "use strict";

    const canvas = document.getElementById("average-chart");
    const valueElement = document.getElementById("chart-value");
    const timeElement = document.getElementById("chart-time");
    const buttons = document.querySelectorAll(".chart-button");

    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    let allPoints = [];
    let visiblePoints = [];
    let selectedHours = 1;
    let hoverIndex = -1;

    const money = value => Number(value).toLocaleString(
        "en-US",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );

    const timeLabel = value => new Date(value).toLocaleString(
        "en-GB",
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );

    function filterPoints() {
        const cutoff = Date.now() - selectedHours * 3600000;

        visiblePoints = allPoints.filter(
            point => point.time >= cutoff
        );

        hoverIndex = -1;
        updateValue();
        draw();
    }

    function updateValue() {
        if (!visiblePoints.length) {
            valueElement.textContent = "No data";
            timeElement.textContent =
                "Waiting for market history...";
            return;
        }

        const point = hoverIndex >= 0
            ? visiblePoints[hoverIndex]
            : visiblePoints[visiblePoints.length - 1];

        valueElement.textContent = money(point.price);
        timeElement.textContent =
            (hoverIndex >= 0 ? "Selected: " : "Latest: ") +
            timeLabel(point.time);
    }

    function draw() {
        const rect = canvas.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;

        if (!width || !height) return;

        const dpr = window.devicePixelRatio || 1;

        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);

        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, width, height);

        const left = 72;
        const right = 18;
        const top = 20;
        const bottom = 38;

        const plotWidth = Math.max(1, width - left - right);
        const plotHeight = Math.max(1, height - top - bottom);

        if (!visiblePoints.length) {
            ctx.fillStyle = "#94a3b8";
            ctx.font = "14px Arial";
            ctx.fillText("No data for this period", left, height / 2);
            return;
        }

        const prices = visiblePoints.map(p => p.price);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const padding = Math.max((maxPrice - minPrice) * 0.15, 0.5);

        const minY = minPrice - padding;
        const maxY = maxPrice + padding;

        const firstTime = visiblePoints[0].time;
        const lastTime = visiblePoints[visiblePoints.length - 1].time;
        const timeSpan = Math.max(1, lastTime - firstTime);

        const x = point => left +
            ((point.time - firstTime) / timeSpan) * plotWidth;

        const y = point => top +
            ((maxY - point.price) / (maxY - minY)) * plotHeight;

        ctx.font = "12px Arial";
        ctx.lineWidth = 1;

        for (let i = 0; i <= 4; i++) {
            const yy = top + (plotHeight / 4) * i;
            const price = maxY - ((maxY - minY) / 4) * i;

            ctx.strokeStyle = "#334155";
            ctx.beginPath();
            ctx.moveTo(left, yy);
            ctx.lineTo(width - right, yy);
            ctx.stroke();

            ctx.fillStyle = "#94a3b8";
            ctx.textAlign = "right";
            ctx.fillText(money(price), left - 10, yy + 4);
        }

        ctx.fillStyle = "#94a3b8";
        ctx.textAlign = "center";

        for (let i = 0; i <= 4; i++) {
            const timestamp = firstTime + (timeSpan / 4) * i;
            const xx = left + (plotWidth / 4) * i;

            ctx.fillText(
                new Date(timestamp).toLocaleTimeString(
                    "en-GB",
                    {hour: "2-digit", minute: "2-digit"}
                ),
                xx,
                height - 12
            );
        }

        const gradient = ctx.createLinearGradient(
            0, top, 0, height - bottom
        );

        gradient.addColorStop(0, "rgba(96,165,250,0.30)");
        gradient.addColorStop(1, "rgba(96,165,250,0)");

        ctx.beginPath();
        visiblePoints.forEach((point, index) => {
            if (index === 0) {
                ctx.moveTo(x(point), y(point));
            } else {
                ctx.lineTo(x(point), y(point));
            }
        });

        ctx.lineTo(x(visiblePoints[visiblePoints.length - 1]),
                   height - bottom);
        ctx.lineTo(x(visiblePoints[0]), height - bottom);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        ctx.beginPath();
        visiblePoints.forEach((point, index) => {
            if (index === 0) {
                ctx.moveTo(x(point), y(point));
            } else {
                ctx.lineTo(x(point), y(point));
            }
        });

        ctx.strokeStyle = "#60a5fa";
        ctx.lineWidth = 2.5;
        ctx.lineJoin = "round";
        ctx.stroke();

        if (hoverIndex >= 0) {
            const point = visiblePoints[hoverIndex];
            const xx = x(point);
            const yy = y(point);

            ctx.beginPath();
            ctx.moveTo(xx, top);
            ctx.lineTo(xx, height - bottom);
            ctx.strokeStyle = "#64748b";
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.beginPath();
            ctx.arc(xx, yy, 5, 0, Math.PI * 2);
            ctx.fillStyle = "#ffffff";
            ctx.fill();
            ctx.strokeStyle = "#60a5fa";
            ctx.lineWidth = 3;
            ctx.stroke();
        }
    }

    canvas.addEventListener("mousemove", event => {
        if (!visiblePoints.length) return;

        const rect = canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const plotWidth = Math.max(1, rect.width - 90);

        const firstTime = visiblePoints[0].time;
        const lastTime = visiblePoints[visiblePoints.length - 1].time;
        const span = Math.max(1, lastTime - firstTime);

        let nearest = 0;
        let distance = Infinity;

        visiblePoints.forEach((point, index) => {
            const xx = 72 +
                ((point.time - firstTime) / span) * plotWidth;
            const delta = Math.abs(mouseX - xx);

            if (delta < distance) {
                distance = delta;
                nearest = index;
            }
        });

        hoverIndex = nearest;
        updateValue();
        draw();
    });

    canvas.addEventListener("mouseleave", () => {
        hoverIndex = -1;
        updateValue();
        draw();
    });

    buttons.forEach(button => {
        button.addEventListener("click", () => {
            selectedHours = Number(button.dataset.hours);

            buttons.forEach(b => b.classList.remove("active"));
            button.classList.add("active");

            filterPoints();
        });
    });

    async function loadAverageHistory() {
        try {
            const response = await fetch(
                "/prices/average-history?limit=1000",
                {cache: "no-store"}
            );

            if (!response.ok) {
                throw new Error("History API unavailable");
            }

            const data = await response.json();

            allPoints = data.prices
                .map(item => ({
                    time: new Date(item.recorded_at).getTime(),
                    price: Number(item.average_price)
                }))
                .filter(point =>
                    Number.isFinite(point.time) &&
                    Number.isFinite(point.price)
                )
                .sort((a, b) => a.time - b.time);

            filterPoints();
        } catch (error) {
            console.error("Chart error:", error);
            timeElement.textContent =
                "Unable to load price history";
        }
    }

    window.addEventListener("resize", draw);

    window.addEventListener(
        "cryptowatch:refresh-chart",
        loadAverageHistory
    );

    loadAverageHistory();
    setInterval(loadAverageHistory, 30000);
})();
