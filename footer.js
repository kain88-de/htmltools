const currentPath = window.location.pathname;
const fileName = (currentPath.split("/").pop() || "index").replace(/\/$/, "") || "index";
const htmlFileName = fileName.endsWith(".html") ? fileName : `${fileName}.html`;
const slug = htmlFileName.replace(/\.html$/, "");

async function loadJson(relativePath) {
  const url = new URL(relativePath, import.meta.url);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${relativePath}`);
  }
  return response.json();
}

function createLink(label, href) {
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.textContent = label;
  anchor.style.color = "inherit";
  anchor.style.textDecoration = "underline";
  return anchor;
}

async function mountFooter() {
  const footer = document.createElement("footer");
  footer.style.marginTop = "2rem";
  footer.style.paddingTop = "1rem";
  footer.style.borderTop = "1px solid rgba(0, 0, 0, 0.16)";
  footer.style.fontFamily = 'system-ui, sans-serif';
  footer.style.fontSize = "0.9rem";

  const row = document.createElement("nav");
  row.style.display = "flex";
  row.style.flexWrap = "wrap";
  row.style.gap = "0.75rem 1rem";

  row.appendChild(createLink("Home", "index.html"));
  row.appendChild(createLink(`About ${slug}`, `${slug}.docs.md`));

  try {
    const config = await loadJson("site-config.json");
    if (config.repo_url) {
      row.appendChild(createLink("View source", `${config.repo_url}/blob/main/${htmlFileName}`));
      row.appendChild(createLink("Changes", `${config.repo_url}/commits/main/${htmlFileName}`));
    }
  } catch (_error) {
    // Keep the footer minimal when repo metadata is unavailable.
  }

  try {
    const dates = await loadJson("dates.json");
    if (dates[htmlFileName]) {
      const stamp = document.createElement("span");
      stamp.textContent = `Updated ${dates[htmlFileName]}`;
      stamp.style.opacity = "0.75";
      row.appendChild(stamp);
    }
  } catch (_error) {
    // Ignore missing dates metadata.
  }

  footer.appendChild(row);
  document.body.appendChild(footer);
}

mountFooter();
