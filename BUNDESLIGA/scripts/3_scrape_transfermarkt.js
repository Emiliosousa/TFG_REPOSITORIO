const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const OUTPUT_FILE = path.join(__dirname, '../data/processed/market_values_raw.json');

(async () => {
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36');
    await page.setViewport({ width: 1366, height: 768 });

    const results = {};
    const YEARS = Array.from({ length: 17 }, (_, i) => 2010 + i); // 2010 to 2026

    console.log("🚀 Starting Bundesliga Transfermarkt Historical Scraping...");

    let cookieClicked = false;

    for (const year of YEARS) {
        // Bundesliga ID = L1
        const url = `https://www.transfermarkt.co.uk/bundesliga/startseite/wettbewerb/L1/plus/?saison_id=${year}`;
        console.log(`\n📅 Scraping Season Start ${year}...`);

        try {
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

            if (!cookieClicked) {
                try {
                    const frames = page.frames();
                    const consentFrame = frames.find(f => f.url().includes('consent'));
                    if (consentFrame) {
                        await consentFrame.click('button[title="Accept & continue"]');
                        cookieClicked = true;
                        await new Promise(r => setTimeout(r, 2000));
                    } else {
                        const btn = await page.$('button[title="Accept & continue"]');
                        if (btn) {
                            await btn.click();
                            cookieClicked = true;
                            await new Promise(r => setTimeout(r, 2000));
                        }
                    }
                } catch (e) { /* Ignore if no cookie banner */ }
            }

            await page.evaluate(() => window.scrollTo(0, 500));
            await new Promise(r => setTimeout(r, 1000));

            const teams = await page.evaluate(() => {
                const rows = document.querySelectorAll('table.items tbody tr');
                const data = {};

                rows.forEach(row => {
                    const nameLink = row.querySelector('td.hauptlink a');
                    const valueLink = row.querySelector('td.rechts.hauptlink a');

                    if (nameLink && valueLink) {
                        const name = nameLink.textContent.trim();
                        let valueRaw = valueLink.textContent.trim();

                        let value = 0;
                        if (valueRaw.includes('bn')) {
                            value = parseFloat(valueRaw.replace(/[^0-9.]/g, '')) * 1000;
                        } else if (valueRaw.includes('m')) {
                            value = parseFloat(valueRaw.replace(/[^0-9.]/g, ''));
                        } else if (valueRaw.includes('k')) {
                            value = parseFloat(valueRaw.replace(/[^0-9.]/g, '')) / 1000;
                        }

                        if (name && value > 0) {
                            data[name] = value;
                        }
                    }
                });
                return data;
            });

            console.log(`   -> Found ${Object.keys(teams).length} teams.`);
            results[year] = teams;

            await new Promise(r => setTimeout(r, 3000));

        } catch (e) {
            console.error(`❌ Error scraping ${year}: ${e.message}`);
        }
    }

    await browser.close();

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));
    console.log(`\n💾 Saved values to ${OUTPUT_FILE}`);

})();
