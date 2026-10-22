// Low-level API example only. For the actual Nicepage form use nicepage-embed.html.
// Deploy only on a separately authenticated Nicepage page; JavaScript is not authentication.
const DATA_ROOT = 'https://wiced.github.io/vesselsanctions/data';
const MAX_AGE_DAYS = 7;
let sanctionsCache = null;
let sanctionsCacheLoadedAt = 0;
const CACHE_MS = 5 * 60 * 1000;

async function loadSanctions() {
  const [statusResponse, dataResponse] = await Promise.all([
    fetch(`${DATA_ROOT}/status.json`, {cache: 'no-store'}),
    fetch(`${DATA_ROOT}/vessels.json`, {cache: 'no-store'})
  ]);
  if (!statusResponse.ok || !dataResponse.ok) throw Error('Data source unavailable');
  const [status, data] = await Promise.all([statusResponse.json(), dataResponse.json()]);
  const ageDays = (Date.now() - Date.parse(status.generated_at)) / 86400000;
  if (!status.ready || !Number.isFinite(ageDays) || ageDays < -0.1 || ageDays > MAX_AGE_DAYS) {
    throw Error('Sanctions list is stale or not initialized');
  }
  if (['EU', 'OFAC', 'UK'].some(source => !status.sources?.[source])) {
    throw Error('Missing sanctions source');
  }
  if (status.generated_at !== data.generated_at) throw Error('Dataset mismatch');
  sanctionsCache = data;
  sanctionsCacheLoadedAt = Date.now();
  return data;
}

async function checkIMO(input) {
  const imo = String(input).trim().replace(/^IMO\s*/i, '');
  if (!/^\d{7}$/.test(imo)) return {status: 'INVALID_IMO', imo};
  try {
    const data = (sanctionsCache && Date.now() - sanctionsCacheLoadedAt < CACHE_MS)
      ? sanctionsCache : await loadSanctions();
    const ship = data.vessels?.[imo];
    if (!ship) return {status: 'NO_LIST_MATCH', imo, checkedAgainst: ['EU','OFAC','UK'], dataAt: data.generated_at};
    return {status: 'MATCH', imo, ship, dataAt: data.generated_at};
  } catch (err) {
    return {status: 'UNAVAILABLE', imo, message: err.message};
  }
}
// Wire `checkIMO` to the existing Nicepage form. Render text with textContent,
// not innerHTML, to avoid injecting untrusted upstream vessel names.
// MATCH: show matching source/program; NO_LIST_MATCH: not found in checked lists.
// UNAVAILABLE: block normal/negative screening response, show an error.
