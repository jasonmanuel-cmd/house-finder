// Token-authenticated leads API for the private seller dashboard.
// Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ADMIN_TOKEN (required).
// GET /api/leads?min_score=&source=&status=&city=&q=&limit=&offset=
// PATCH /api/leads  {id, status}
export const config = { runtime: 'nodejs' };

const ALLOWED_STATUS = ['new', 'contacted', 'skipped', 'dead', 'won'];

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...extraHeaders },
  });
}

function authed(request) {
  const expected = process.env.ADMIN_TOKEN;
  if (!expected) return { ok: false, why: 'not_configured' };
  const header = request.headers.get('authorization') || '';
  const bearer = header.startsWith('Bearer ') ? header.slice(7) : '';
  const param = new URL(request.url).searchParams.get('token') || '';
  const supplied = bearer || param;
  if (!supplied) return { ok: false, why: 'missing' };
  const a = Buffer.from(supplied), b = Buffer.from(expected);
  const ok = a.length === b.length && crypto.timingSafeEqual(a, b);
  return { ok, why: ok ? 'ok' : 'invalid' };
}

async function supabase(path, init = {}) {
  const url = `${process.env.SUPABASE_URL}/rest/v1${path}`;
  const headers = {
    apikey: process.env.SUPABASE_SERVICE_ROLE_KEY,
    Authorization: `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`,
    'Content-Type': 'application/json',
    ...init.headers,
  };
  const response = await fetch(url, { ...init, headers });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Supabase ${response.status}: ${body.slice(0, 300)}`);
  }
  return response;
}

export default async function handler(request) {
  const auth = authed(request);
  if (!auth.ok) {
    if (auth.why === 'not_configured') return json({ error: 'ADMIN_TOKEN not configured' }, 503);
    return json({ error: 'unauthorized' }, 401, { 'WWW-Authenticate': 'Bearer' });
  }

  const url = new URL(request.url);

  try {
    if (request.method === 'GET') {
      const params = new URLSearchParams();
      const minScore = url.searchParams.get('min_score');
      const source = url.searchParams.get('source');
      const status = url.searchParams.get('status');
      const city = url.searchParams.get('city');
      const q = url.searchParams.get('q');
      const limit = Math.min(parseInt(url.searchParams.get('limit') || '200', 10) || 200, 1000);
      const offset = parseInt(url.searchParams.get('offset') || '0', 10) || 0;

      if (minScore) params.set('deal_score', `gte.${minScore}`);
      if (source) params.set('source', `eq.${source}`);
      if (status) params.set('status', `eq.${status}`);
      if (city) params.set('city', `ilike.%${city.replace(/[%_]/g, '')}%`);
      if (q) params.set('or', `(address.ilike.*${q.replace(/[%_*]/g, '')}*,owner_name.ilike.*${q.replace(/[%_*]/g, '')}*,description.ilike.*${q.replace(/[%_*]/g, '')}*)`);
      params.set('order', 'deal_score.desc,updated_at.desc');
      params.set('select', '*');
      params.set('limit', String(limit));
      params.set('offset', String(offset));

      const [leadsRes, countRes] = await Promise.all([
        supabase(`/private_seller_leads?${params}`),
        supabase(`/private_seller_leads?${params}&select=id`, { headers: { Prefer: 'count=exact' } }),
      ]);
      const leads = await leadsRes.json();
      const total = parseInt(countRes.headers.get('content-range')?.split('/')[1] || '0', 10);
      return json({ leads, total, limit, offset });
    }

    if (request.method === 'PATCH') {
      const body = await request.json().catch(() => null);
      const { id, status } = body || {};
      if (!id || !ALLOWED_STATUS.includes(status)) {
        return json({ error: 'invalid body: need {id, status in ' + ALLOWED_STATUS.join('|') + '}' }, 400);
      }
      const response = await supabase(`/private_seller_leads?id=eq.${encodeURIComponent(id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Prefer: 'return=representation' },
        body: JSON.stringify({ status, updated_at: new Date().toISOString() }),
      });
      const updated = await response.json();
      if (!updated.length) return json({ error: 'not found' }, 404);
      return json({ lead: updated[0] });
    }

    return json({ error: 'method not allowed' }, 405);
  } catch (error) {
    return json({ error: String(error.message || error) }, 502);
  }
}

export const fetch = handler;
