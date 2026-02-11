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

    console.log("🚀 Starting Transfermarkt Historical Scraping...");

    // Cookie Consent Clicker (Run once)
    let cookieClicked = false;

    for (const year of YEARS) {
        // Premier League ID = GB1
        const url = `https://www.transfermarkt.co.uk/premier-league/startseite/wettbewerb/GB1/plus/?saison_id=${year}`;
        console.log(`\n📅 Scraping Season Start ${year}...`);

        try {
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

            // Cookie Consent
            if (!cookieClicked) {
                try {
                    const frames = page.frames();
                    const consentFrame = frames.find(f => f.url().includes('consent'));
                    if (consentFrame) {
                        await consentFrame.click('button[title="Accept & continue"]');
                        cookieClicked = true;
                        await new Promise(r => setTimeout(r, 2000));
                    } else {
                        // Try main page button
                        const btn = await page.$('button[title="Accept & continue"]');
                        if (btn) {
                            await btn.click();
                            cookieClicked = true;
                            await new Promise(r => setTimeout(r, 2000));
                        }
                    }
                } catch (e) { /* Ignore if no cookie banner */ }
            }

            // Scroll to load lazy elements
            await page.evaluate(() => window.scrollTo(0, 500));
            await new Promise(r => setTimeout(r, 1000));

            // Extract Data
            const teams = await page.evaluate(() => {
                // Table selector: table.items
                const rows = document.querySelectorAll('table.items tbody tr');
                const data = {};

                rows.forEach(row => {
                    // Team Name: td.hauptlink.no-border-links a (first hauptlink)
                    // Market Value: td.rechts.hauptlink a (total value)

                    const nameLink = row.querySelector('td.hauptlink a');
                    // Value is usually in the last column, which has class 'rechts hauptlink' or similar
                    const valueLink = row.querySelector('td.rechts.hauptlink a');

                    if (nameLink && valueLink) {
                        const name = nameLink.textContent.trim();
                        let valueRaw = valueLink.textContent.trim();

                        // Parse Value: "€1.20bn", "€500.00m"
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

            // Helpful delay
            await new Promise(r => setTimeout(r, 3000));

        } catch (e) {
            console.error(`❌ Error scraping ${year}: ${e.message}`);
        }
    }

    await browser.close();

    // Save
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));
    console.log(`\n💾 Saved values to ${OUTPUT_FILE}`);

})();
