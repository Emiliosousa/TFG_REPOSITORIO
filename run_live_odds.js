const puppeteer = require('puppeteer');
const fs = require('fs');

async function main() {
    console.log("Starting Visual Winamax Scraper (La Liga + Supercopa)...");
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1280,800']
    });
    const page = await browser.newPage();

    // Set viewport to ensure elements are visible
    await page.setViewport({ width: 1280, height: 800 });

    try {
        // 1. Scraping La Liga
        console.log("Navigating to La Liga...");
        await page.goto('https://www.winamax.es/apuestas-deportivas/futbol/espana/laliga', { waitUntil: 'networkidle2', timeout: 60000 });

        // Close any modals
        try {
            const closeBtn = await page.$('button[class*="close"], div[class*="close"]');
            if (closeBtn) await closeBtn.click();
        } catch (e) { /* ignore */ }

        // Scroll to load all matches
        await autoScroll(page);

        // Extract La Liga Matches
        console.log("Extracting La Liga matches...");
        let matches = await extractMatches(page);
        console.log(`Found ${matches.length} matches in La Liga.`);

        // 2. Check for Supercopa / Copa del Rey (for El Clasico)
        console.log("Checking for Supercopa/Copa...");
        const supercopaFound = await page.evaluate(() => {
            const links = Array.from(document.querySelectorAll('a, span, div'));
            const target = links.find(el => el.innerText.includes('Supercopa') || el.innerText.includes('Copa del Rey'));
            if (target) {
                target.click();
                return true;
            }
            return false;
        });

        if (supercopaFound) {
            console.log("Navigated to Supercopa section. Waiting for load...");
            await new Promise(r => setTimeout(r, 2000));

            // Scroll again
            await autoScroll(page);

            console.log("Extracting Supercopa matches...");
            const cupMatches = await extractMatches(page);
            console.log(`Found ${cupMatches.length} matches in Supercopa.`);

            // Merge unique matches
            for (const m of cupMatches) {
                const key = `${m.home_team} vs ${m.away_team}`;
                if (!matches.find(ex => `${ex.home_team} vs ${ex.away_team}` === key)) {
                    matches.push(m);
                }
            }
        }

        // Final Filter for User's WhiteList/BlackList preference
        // (Though our extractMatches handles the whitelist, we double check here if needed)

        if (matches.length > 0) {
            fs.writeFileSync('live_odds.json', JSON.stringify(matches, null, 2));
            console.log(`✅ MATCHES SAVED: ${matches.length}`);
            console.log(JSON.stringify(matches, null, 2));
        } else {
            console.error("⚠️ No matches found! Check debug screenshots.");
        }

    } catch (e) {
        console.error("❌ Error during scraping:", e);
    } finally {
        await browser.close();
    }
}

async function extractMatches(page) {
    return await page.evaluate(() => {
        const LALIGA_TEAMS = [
            "Alavés", "Athletic Bilbao", "Athletic", "Atlético Madrid", "Atlético", "Barcelona", "FC Barcelona", "Betis", "Real Betis",
            "Celta Vigo", "Celta", "Espanyol", "Getafe", "Girona", "Las Palmas", "Leganés", "Mallorca", "RCD Mallorca",
            "Osasuna", "Rayo Vallecano", "Rayo", "Real Madrid", "Real Sociedad", "Sevilla FC", "Sevilla", "Valencia",
            "Valladolid", "Villarreal", "Elche", "Levante", "Cádiz", "Almería", "Granada"
        ];

        const results = [];
        const seenMatches = new Set();

        // Find all match cards (divs that strictly contain 3 odds)
        const divs = document.querySelectorAll('div');
        divs.forEach(div => {
            // Get text lines
            const text = div.innerText;
            if (!text) return;

            const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);

            // Check for Odds pattern (e.g. "1,50" or "2.30")
            // We look for lines that are purely decimal numbers
            const oddsLines = lines.filter(l => /^\d+[,.]\d{2}$/.test(l));

            if (oddsLines.length >= 3) {
                // This div contains odds. Let's see if it has 2 La Liga teams.

                // We scan the lines IN ORDER to find teams.
                const foundTeams = [];
                for (const line of lines) {
                    // Check if this line allows as a team name
                    // We match against our whitelist
                    const cleanLine = line.toLowerCase();
                    const match = LALIGA_TEAMS.find(t => cleanLine === t.toLowerCase() || cleanLine.includes(t.toLowerCase()));

                    if (match) {
                        // Avoid adding the same team twice immediately (some cards repeat names)
                        if (foundTeams.length === 0 || foundTeams[foundTeams.length - 1] !== match) {
                            // Map 'Athletic' -> 'Athletic Bilbao' etc if needed, or just keep name found
                            // For dashboard consistency, we might want to normalize, but for now scrape raw
                            foundTeams.push(match);
                        }
                    }
                }

                // We need at least 2 distinct teams
                const distinctTeams = [...new Set(foundTeams)]; // Simple dedup

                if (distinctTeams.length >= 2) {
                    // We assume the first 2 distinct teams found are Home vs Away
                    const home = distinctTeams[0];
                    const away = distinctTeams[1];

                    // Filter out Women's teams if noted (usually (F) or distinctive names)
                    if (home.includes('(F)') || away.includes('(F)')) return;

                    // Extract odds (first 3 found)
                    const o1 = parseFloat(oddsLines[0].replace(',', '.'));
                    const ox = parseFloat(oddsLines[1].replace(',', '.'));
                    const o2 = parseFloat(oddsLines[2].replace(',', '.'));

                    const matchKey = `${home} vs ${away}`;

                    if (!seenMatches.has(matchKey)) {
                        results.push({
                            home_team: home.charAt(0).toUpperCase() + home.slice(1), // Capitalize
                            away_team: away.charAt(0).toUpperCase() + away.slice(1),
                            odds_1: o1,
                            odds_x: ox,
                            odds_2: o2,
                            match_date: "Upcoming" // Placeholder, difficult to parse date reliably without specific selectors
                        });
                        seenMatches.add(matchKey);
                    }
                }
            }
        });

        return results;
    });
}

async function autoScroll(page) {
    await page.evaluate(async () => {
        await new Promise((resolve) => {
            var totalHeight = 0;
            var distance = 100;
            var timer = setInterval(() => {
                var scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;

                if (totalHeight >= scrollHeight - window.innerHeight) {
                    clearInterval(timer);
                    resolve();
                }
            }, 100);
        });
    });
}

main();
