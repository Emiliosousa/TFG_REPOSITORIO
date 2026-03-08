const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const OUTPUT_FILE = path.join(__dirname, '../state_dump.json');
// Bundesliga on Winamax España: sport 1 (football), category 30 (Germany), tournament 1 (Bundesliga)
const URL = 'https://www.winamax.es/apuestas-deportivas/sports/1/30/2036';

(async () => {
    console.log("Launching Winamax Scraper for Bundesliga (Puppeteer)...");
    let browser;
    try {
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

        console.log(`Navigating to ${URL}...`);
        await page.goto(URL, { waitUntil: 'networkidle2', timeout: 90000 });

        console.log("Extracting state...");
        const state = await page.evaluate(() => {
            if (window.PRELOADED_STATE) return window.PRELOADED_STATE;
            return null;
        });

        if (!state || !state.matches) {
            throw new Error("Could not find PRELOADED_STATE or matches data.");
        }

        console.log("State extracted.");
        fs.writeFileSync(OUTPUT_FILE, JSON.stringify(state, null, 2));
        console.log(`Saved raw state to ${OUTPUT_FILE}`);

    } catch (error) {
        console.error("Scraper Error:", error.message);
        process.exit(1);
    } finally {
        if (browser) await browser.close();
    }
})();
