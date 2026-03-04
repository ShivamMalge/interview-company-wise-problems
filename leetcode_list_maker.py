import os
import csv
import json

def get_slugs_from_csv(filename):
    slugs = []
    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                link = row.get("Link", "")
                if "leetcode.com/problems/" in link:
                    slug = link.split("leetcode.com/problems/")[1].strip("/")
                    slugs.append(slug)
    except Exception:
        pass
    return slugs

def main():
    base_dir = input("Enter the path to the main repository folder (or '.' for current directory): ").strip()
    if not os.path.isdir(base_dir):
        print("Invalid directory.")
        return

    seen_slugs = set()
    companies_data = []

    for item in os.listdir(base_dir):
        company_path = os.path.join(base_dir, item)
        if os.path.isdir(company_path):
            csv_path = os.path.join(company_path, "5. All.csv")
            if os.path.exists(csv_path):
                raw_slugs = get_slugs_from_csv(csv_path)
                unique_slugs = []
                for s in raw_slugs:
                    if s not in seen_slugs:
                        unique_slugs.append(s)
                        seen_slugs.add(s)
                
                if unique_slugs:
                    companies_data.append({
                        "company": item,
                        "slugs": unique_slugs
                    })

    if not companies_data:
        print("No valid folders or questions found.")
        return

    js_data = json.dumps(companies_data)
    output_file = "master_console_script.js"

    js_template = f"""
async function processAllCompanies() {{
    const data = {js_data};
    const getCookie = (name) => {{
        const value = `; ${{document.cookie}}`;
        const parts = value.split(`; ${{name}}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }};
    
    const csrfToken = getCookie('csrftoken');

    const createQuery = `mutation createEmptyFavorite($description: String, $favoriteType: FavoriteTypeEnum!, $isPublicFavorite: Boolean = true, $name: String!) {{
        createEmptyFavorite(description: $description, favoriteType: $favoriteType, isPublicFavorite: $isPublicFavorite, name: $name) {{
            ok
            error
            favoriteSlug
        }}
    }}`;

    const addQuery = `mutation batchAddQuestionsToFavorite($favoriteSlug: String!, $questionSlugs: [String]!) {{
        batchAddQuestionsToFavorite(favoriteSlug: $favoriteSlug, questionSlugs: $questionSlugs) {{
            ok
            error
        }}
    }}`;

    for (const item of data) {{
        if (item.slugs.length === 0) continue;
        console.log(`Creating list for ${{item.company}}...`);

        try {{
            const createRes = await fetch("https://leetcode.com/graphql/", {{
                method: "POST",
                headers: {{
                    "content-type": "application/json",
                    "x-csrftoken": csrfToken
                }},
                body: JSON.stringify({{
                    operationName: "createEmptyFavorite",
                    variables: {{
                        name: item.company,
                        description: "Auto-generated list",
                        favoriteType: "NORMAL",
                        isPublicFavorite: true
                    }},
                    query: createQuery
                }})
            }});
            
            const createJson = await createRes.json();
            const listSlug = createJson.data?.createEmptyFavorite?.favoriteSlug;

            if (listSlug) {{
                console.log(`Adding ${{item.slugs.length}} questions to ${{item.company}}...`);
                await fetch("https://leetcode.com/graphql/", {{
                    method: "POST",
                    headers: {{
                        "content-type": "application/json",
                        "x-csrftoken": csrfToken
                    }},
                    body: JSON.stringify({{
                        operationName: "batchAddQuestionsToFavorite",
                        variables: {{
                            favoriteSlug: listSlug,
                            questionSlugs: item.slugs
                        }},
                        query: addQuery
                    }})
                }});
                console.log(`%cSuccess for ${{item.company}}!`, "color: green");
            }} else {{
                console.log(`%cFailed to create list for ${{item.company}}`, "color: red");
            }}
        }} catch (err) {{
            console.log(`%cError on ${{item.company}}:`, "color: red", err.message);
        }}
        
        await new Promise(r => setTimeout(r, 2000));
    }}
    console.log("%cAll companies processed successfully!", "color: blue; font-size: 16px; font-weight: bold;");
}}

processAllCompanies();
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(js_template.strip())

    print(f"Successfully processed {len(companies_data)} companies.")
    print(f"Total unique questions queued: {len(seen_slugs)}")
    print(f"Generated {output_file}. Paste it into your console!")

if __name__ == "__main__":
    main()
