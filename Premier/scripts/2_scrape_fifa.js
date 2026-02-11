const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const OUTPUT_FILE = path.join(__dirname, '../data/processed/fifa_ratings_raw.json');

// Mapped from previous exploration
const ROSTERS = {
    2026: '260016', // FC 26
    2025: '250044', // FC 25
    2024: '240050', // FC 24
    2023: '230054', // FIFA 23
    2022: '220069', // FIFA 22
    2021: '210064', // FIFA 21
    2020: '200061', // FIFA 20
    2019: '190075', // FIFA 19
    2018: '180084', // FIFA 18
    2017: '170099', // FIFA 17
    2016: '160058', // FIFA 16
    2015: '150059', // FIFA 15
    2014: '140052', // FIFA 14
    2013: '130034', // FIFA 13
    2012: '120002', // FIFA 12
    2011: '110002', // FIFA 11
    2010: '100002', // FIFA 10
};

(async () => {
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
    await page.setViewport({ width: 1366, height: 768 });

    const results = {};

    console.log("🚀 Starting SoFIFA Historical Scraping...");

    for (const [year, rosterId] of Object.entries(ROSTERS)) {
        // Construct URL: Premier League ID = 13
        const url = `https://sofifa.com/teams?type=club&lg=13&r=${rosterId}&set=true`;
        console.log(`\n📅 Scraping ${year} (Roster: ${rosterId})...`);

        try {
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });

            // Extract Data
            const teams = await page.evaluate(() => {
                const rows = document.querySelectorAll('table tbody tr');
                const data = {};

                rows.forEach(row => {
                    // Selector based on inspection: Name is usually in 2nd col (a link to /team/), Rating in 3rd col (span/div)
                    const nameLink = row.querySelector('td:nth-child(2) a[href^="/team/"]');
                    const ratingCell = row.querySelector('td:nth-child(3)');

                    if (nameLink && ratingCell) {
                        const name = nameLink.textContent.trim();
                        // Rating is often "85", sometimes inside a span, assume text content is enough
                        const rating = parseInt(ratingCell.textContent.trim().replace(/\D/g, '')); // clean non-digits

                        if (name && !isNaN(rating)) {
                            data[name] = rating;
                        }
                    }
                });
                return data;
            });

            console.log(`   -> Found ${Object.keys(teams).length} teams.`);
            results[year] = teams;

            // Random delay to be polite
            await new Promise(r => setTimeout(r, 2000));

        } catch (e) {
            console.error(`❌ Error scraping ${year}: ${e.message}`);
        }
    }

    await browser.close();

    // Save
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));
    console.log(`\n💾 Saved ratings to ${OUTPUT_FILE}`);

})();
