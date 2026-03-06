import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════
   MWT.ONE — Invoice de Comisiones (Tipo 2)
   Audience: Marluvas (Brasil) — wire transfer claim
   Unified design system + gate signature + @media print
   ═══════════════════════════════════════════════════════════════════════════ */

// ── DESIGN TOKENS (shared across all MWT documents) ──────────────────────
const T = {
  navy: "#013A57", navyLight: "#01496E", navyDark: "#012A40",
  mint: "#75CBB3", mintLight: "#A8E6D1", mintDark: "#5BA899",
  ice: "#A8D8EA", iceSoft: "#D4ECFA",
  bg: "#F5F7FA", surface: "#FFFFFF", surfaceHover: "#FAFBFC",
  border: "#E4E8EE", borderStrong: "#CBD2DA",
  txt1: "#013A57", txt2: "#3D5060", txt3: "#7A8E9E",
  ok: "#0E8A6D", okBg: "#EDFAF5",
  warn: "#B45309", warnBg: "#FFF8ED",
  crit: "#DC2626", critBg: "#FEF2F2",
  font: "'Plus Jakarta Sans', system-ui, sans-serif",
  mono: "'JetBrains Mono', monospace",
};

const PRINT_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
  @media print {
    /* B1 */ * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
    /* B2 */ .no-print { display: none !important; }
    /* B3 */ .print-only { display: block !important; }
    /* B4 */ @page { margin: 6mm 8mm; size: letter; }
    /* B5 */ body, html { background: white !important; font-size: 11px; }
    .page-root { background: white !important; padding: 0 !important; max-width: 100% !important; }
    /* B6 */ table { font-size: 10px; }
    table thead th { font-size: 8.5px; padding: 6px 8px; background: #f1f5f9 !important; border-bottom: 2px solid #999 !important; }
    table tbody td { padding: 6px 8px; }
    /* B7 */ .card-wrap { border: 1px solid #ccc !important; margin-bottom: 10px; }
    .card-grid { border: 1px solid #ccc !important; }
    /* B9 */ .card-wrap, .card-grid, table { break-inside: avoid; page-break-inside: avoid; }
    table tr { break-inside: avoid; }
    /* B13 */ a { text-decoration: none; color: inherit; }
  }
  @media screen { .print-only { display: none !important; } }
`;

// ── SAMPLE DATA ──────────────────────────────────────────────────────────
const DATA = {
  number: "MWT-0094", date: "March 4, 2026", currency: "USD", terms: "Due upon receipt", period: "February 2026",
  emitter: { name: "Muito Work Limitada", taxId: "3-102-751710", jurisdiction: "Costa Rica", address: "Condominio Balcones de la Rivera, Casa 11", city: "La Rivera, Belen, Heredia 40702", country: "Costa Rica", phone: "+506 6043 1300", email: "alvaro@muitowork.com" },
  recipient: { name: "MARLUVAS EQUIPAMENTOS DE SEGURANCA LTDA", taxId: "19.653.054/0001-84", taxLabel: "CNPJ", address: "Rodovia Dores de Campos / Barroso S/N", city: "36213000 Dores de Campos / MG", country: "Brasil" },
  commissions: [
    { client: "Importaciones Y Compras", fatura: "2354-2025", base: 8425.90, rate: 9.37, amount: 789.51 },
    { client: "Importaciones Y Compras", fatura: "2355-2025", base: 33762.50, rate: 10.00, amount: 3376.25 },
    { client: "Imporcomp", fatura: "2365-2025", base: 5829.70, rate: 10.00, amount: 582.97 },
  ],
  premio: { label: "Premio de Vendas", amount: 1201.80, ptax: "5.2500", ptaxDate: "03/03/2026" },
  bank: { name: "First Century Bank", address: "1731 N Elm St, Commerce, GA 30529, USA", swift: "FCNSUS32", aba: "061120084", account: "4022515606926", beneficiary: "Muito Work Limitada" },
  signature: { issuedBy: "mwt.one", issuedAt: "2026-03-04T14:32:00Z", signatureMode: "manual_gate", approvedBy: null, approvedAt: null, autoPolicy: null },
};

// ── HELPERS & SHARED UI ──────────────────────────────────────────────────
const fmt = (n) => n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const Badge = ({ children, color = "navy" }) => {
  const m = { navy: { bg: T.iceSoft, c: T.navy }, mint: { bg: T.okBg, c: T.ok }, warn: { bg: T.warnBg, c: T.warn }, crit: { bg: T.critBg, c: T.crit }, draft: { bg: T.warnBg, c: T.warn } };
  const s = m[color] || m.navy;
  return <span style={{ display: "inline-block", background: s.bg, color: s.c, fontSize: 10, fontWeight: 700, padding: "2px 10px", borderRadius: 20, letterSpacing: 0.3 }}>{children}</span>;
};
const Card = ({ children, style, className = "" }) => <div className={`card-wrap ${className}`} style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 12, overflow: "hidden", ...style }}>{children}</div>;
const Lbl = ({ children }) => <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", color: T.mint, marginBottom: 8 }}>{children}</div>;
const Row = ({ label, value, mono, strong, color }) => (
  <div style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", fontSize: 13 }}>
    <span style={{ color: T.txt3 }}>{label}</span>
    <span style={{ fontWeight: strong ? 700 : 600, color: color || T.txt1, fontFamily: mono ? T.mono : "inherit", fontVariantNumeric: "tabular-nums" }}>{value}</span>
  </div>
);

const SignatureGate = ({ sig }) => (
  <Card style={{ padding: "18px 22px", marginBottom: 20 }} className="no-print">
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5, textTransform: "uppercase", color: T.txt3, marginBottom: 6 }}>Issued By</div>
        <div style={{ fontSize: 13, fontWeight: 600 }}>{sig.issuedBy}</div>
        <div style={{ fontSize: 11, color: T.txt3, fontFamily: T.mono, marginTop: 3 }}>{sig.issuedAt ? new Date(sig.issuedAt).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" }) : "—"}</div>
      </div>
      <div>
        <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5, textTransform: "uppercase", color: T.txt3, marginBottom: 6 }}>{sig.signatureMode === "auto" ? "Auto-Approved" : "Approved By"}</div>
        {sig.approvedBy ? (
          <><div style={{ fontSize: 13, fontWeight: 600 }}>{sig.approvedBy}</div><div style={{ fontSize: 11, color: T.txt3, fontFamily: T.mono, marginTop: 3 }}>{sig.approvedAt ? new Date(sig.approvedAt).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" }) : "—"}</div></>
        ) : sig.signatureMode === "auto" ? (
          <><div style={{ fontSize: 13, fontWeight: 600, color: T.ok }}>Automatic</div><div style={{ fontSize: 11, color: T.txt3, marginTop: 3 }}>Policy: {sig.autoPolicy || "N/A"}</div></>
        ) : (
          <div style={{ padding: "8px 14px", background: T.warnBg, borderRadius: 8, marginTop: 2 }}><div style={{ fontSize: 12, fontWeight: 600, color: T.warn }}>Pending approval</div><div style={{ fontSize: 11, color: T.warn, opacity: 0.8, marginTop: 2 }}>CEO must approve before sending</div></div>
        )}
      </div>
    </div>
  </Card>
);

const Topbar = ({ label, badge, tab, setTab, tabs }) => (
  <div className="no-print" style={{ background: T.navy, padding: "10px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ color: "#fff", fontWeight: 800, fontSize: 16, letterSpacing: -0.5 }}>MWT.ONE</span>
      <span style={{ color: T.mint, fontSize: 10, fontWeight: 600, background: "rgba(117,203,179,0.15)", padding: "2px 10px", borderRadius: 20 }}>{label}</span>
      {badge}
    </div>
    <div style={{ display: "flex", gap: 4 }}>
      {tabs.map(t => (
        <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: "6px 14px", border: "none", borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: T.font, transition: "all 0.15s", background: tab === t.id ? T.mint : "rgba(255,255,255,0.08)", color: tab === t.id ? T.navy : "rgba(255,255,255,0.6)" }}>{t.label}</button>
      ))}
      <button onClick={() => window.print()} style={{ marginLeft: 8, background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)", color: "#fff", padding: "6px 14px", borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: T.font }}>⎙ Print</button>
    </div>
  </div>
);

const Footer = ({ text }) => <div style={{ textAlign: "center", paddingTop: 14, borderTop: `1px solid ${T.border}`, fontSize: 10, color: T.txt3, lineHeight: 1.8 }}>{text}</div>;

// ── EXPANDABLE ROW ───────────────────────────────────────────────────────
const CommissionRow = ({ item, index, expanded, onToggle }) => {
  const isExp = expanded === index;
  return (
    <div style={{ borderBottom: `1px solid ${T.border}`, cursor: "pointer" }} onClick={() => onToggle(isExp ? null : index)}
      onMouseEnter={e => (e.currentTarget.style.background = T.surfaceHover)} onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 120px 80px 100px 30px", padding: "12px 18px", alignItems: "center", gap: 8 }}>
        <div><div style={{ fontSize: 13, fontWeight: 600, color: T.txt1 }}>{item.client}</div><div style={{ fontSize: 11, color: T.txt3, fontFamily: T.mono, marginTop: 2 }}>Fatura {item.fatura}</div></div>
        <div style={{ textAlign: "right", fontSize: 13, color: T.txt2, fontVariantNumeric: "tabular-nums" }}>{fmt(item.base)}</div>
        <div style={{ textAlign: "right" }}><Badge color="mint">{item.rate.toFixed(2)}%</Badge></div>
        <div style={{ textAlign: "right", fontSize: 14, fontWeight: 700, color: T.navy, fontVariantNumeric: "tabular-nums" }}>{fmt(item.amount)}</div>
        <div className="no-print" style={{ textAlign: "right", fontSize: 16, color: T.txt3, transition: "transform 0.2s", transform: isExp ? "rotate(180deg)" : "rotate(0deg)" }}>▾</div>
      </div>
      {isExp && (
        <div className="no-print" style={{ padding: "0 18px 14px 18px", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, borderTop: `1px dashed ${T.border}`, paddingTop: 12 }}>
          <div><div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", color: T.txt3 }}>Calculation</div><div style={{ fontSize: 12, color: T.txt2, marginTop: 4, fontFamily: T.mono }}>{fmt(item.base)} × {item.rate.toFixed(2)}% = {fmt(item.amount)}</div></div>
          <div><div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", color: T.txt3 }}>Source</div><div style={{ fontSize: 12, color: T.txt2, marginTop: 4 }}>Marluvas monthly settlement — Feb 2026</div></div>
          <div><div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", color: T.txt3 }}>Status</div><div style={{ marginTop: 4 }}><Badge color="mint">Verified</Badge></div></div>
        </div>
      )}
    </div>
  );
};

// ══════════════════════════════════════════════════════════════════════════
export default function InvoiceComisiones() {
  const [tab, setTab] = useState("detail");
  const [expanded, setExpanded] = useState(null);
  const d = DATA;
  const commissionsTotal = d.commissions.reduce((s, c) => s + c.amount, 0);
  const baseTotal = d.commissions.reduce((s, c) => s + c.base, 0);
  const grandTotal = commissionsTotal + d.premio.amount;
  const tabs = [{ id: "detail", label: "Detail" }, { id: "summary", label: "Summary" }, { id: "bank", label: "Wire Info" }];

  return (
    <div style={{ fontFamily: T.font, background: T.bg, minHeight: "100vh", color: T.txt1 }}>
      <style>{PRINT_CSS}</style>
      <Topbar label="Invoice" badge={<Badge color="draft">PENDING</Badge>} tab={tab} setTab={setTab} tabs={tabs} />
      <div className="page-root" style={{ maxWidth: 900, margin: "0 auto", padding: "24px 20px 50px" }}>
        {/* Print-only header */}
        <div className="print-only" style={{ textAlign: "center", marginBottom: 16, paddingBottom: 12, borderBottom: `2px solid ${T.navy}` }}>
          <div style={{ fontSize: 18, fontWeight: 800, color: T.navy }}>MUITO WORK LIMITADA</div>
          <div style={{ fontSize: 10, color: T.txt3 }}>International Trade Services · Tax ID 3-102-751710 · Costa Rica</div>
        </div>
        {/* Header */}
        <Card style={{ padding: "24px 28px", marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: 16, borderBottom: `2px solid ${T.navy}`, marginBottom: 16 }}>
            <div><h1 style={{ fontSize: 20, fontWeight: 800, color: T.navy, margin: 0 }}>MUITO WORK LIMITADA</h1><div style={{ fontSize: 11, color: T.txt3, marginTop: 2 }}>International Trade Services</div></div>
            <div style={{ textAlign: "right" }}><div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.5, textTransform: "uppercase", color: T.txt3 }}>Invoice</div><div style={{ fontFamily: T.mono, fontSize: 28, fontWeight: 800, color: T.navy, letterSpacing: -2, lineHeight: 1 }}>{d.number}</div></div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
            {[["Date", d.date], ["Currency", d.currency], ["Period", d.period], ["Terms", d.terms]].map(([l, v], i) => (
              <div key={i}><div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5, textTransform: "uppercase", color: T.txt3, marginBottom: 2 }}>{l}</div><div style={{ fontSize: 13, fontWeight: 600 }}>{v}</div></div>
            ))}
          </div>
        </Card>
        {/* Parties */}
        <div className="card-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 16 }}>
          <Card style={{ padding: "18px 22px" }}><Lbl>From / Emisor</Lbl><div style={{ fontSize: 13, fontWeight: 700, color: T.navy }}>{d.emitter.name}</div><div style={{ fontSize: 11, color: T.txt3, fontFamily: T.mono, marginTop: 2 }}>Tax ID: {d.emitter.taxId} ({d.emitter.jurisdiction})</div><div style={{ fontSize: 11, color: T.txt2, marginTop: 6, lineHeight: 1.5 }}>{d.emitter.address}<br />{d.emitter.city}<br />{d.emitter.country}</div></Card>
          <Card style={{ padding: "18px 22px" }}><Lbl>Bill To / Cliente</Lbl><div style={{ fontSize: 13, fontWeight: 700, color: T.navy }}>{d.recipient.name}</div><div style={{ fontSize: 11, color: T.txt3, fontFamily: T.mono, marginTop: 2 }}>{d.recipient.taxLabel}: {d.recipient.taxId}</div><div style={{ fontSize: 11, color: T.txt2, marginTop: 6, lineHeight: 1.5 }}>{d.recipient.address}<br />{d.recipient.city}<br />{d.recipient.country}</div></Card>
        </div>
        {/* DETAIL */}
        {tab === "detail" && (<>
          <Card style={{ overflow: "hidden", marginBottom: 16 }}>
            <div style={{ padding: "12px 18px", borderBottom: `1px solid ${T.border}`, display: "flex", justifyContent: "space-between" }}><span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5, color: T.navy }}>Agent Commissions</span><span className="no-print" style={{ fontSize: 11, color: T.txt3 }}>{d.commissions.length} items · click to expand</span></div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 120px 80px 100px 30px", padding: "8px 18px", background: "#f1f5f9", borderBottom: `2px solid ${T.borderStrong}` }}>{["Client / Fatura", "Base", "Rate", "Amount", ""].map((h, i) => <div key={i} style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5, textTransform: "uppercase", color: T.txt3, textAlign: i > 0 && i < 4 ? "right" : "left" }}>{h}</div>)}</div>
            {d.commissions.map((item, i) => <CommissionRow key={i} item={item} index={i} expanded={expanded} onToggle={setExpanded} />)}
            <div style={{ background: T.warnBg, padding: "12px 18px", display: "grid", gridTemplateColumns: "1fr 120px 80px 100px 30px", alignItems: "center", borderTop: `1px solid ${T.border}` }}>
              <div><div style={{ fontSize: 13, fontWeight: 600, color: T.warn }}>{d.premio.label}</div><div style={{ fontSize: 10, color: T.warn, opacity: 0.7, marginTop: 2 }}>PTAX {d.premio.ptax} ({d.premio.ptaxDate})</div></div><div /><div /><div style={{ textAlign: "right", fontSize: 14, fontWeight: 700, color: T.warn, fontVariantNumeric: "tabular-nums" }}>{fmt(d.premio.amount)}</div><div />
            </div>
          </Card>
          <Card style={{ padding: "18px 22px", marginBottom: 16 }}>
            <Row label="Commissions" value={`USD ${fmt(commissionsTotal)}`} />
            <Row label="Sales bonus" value={`USD ${fmt(d.premio.amount)}`} />
            <Row label="Tax / IVA" value="USD 0.00" />
            <div style={{ borderTop: `2px solid ${T.navy}`, marginTop: 10, paddingTop: 10, display: "flex", justifyContent: "space-between", alignItems: "baseline" }}><span style={{ fontSize: 16, fontWeight: 800, color: T.navy }}>Total Due</span><span style={{ fontSize: 24, fontWeight: 800, color: T.navy, fontVariantNumeric: "tabular-nums", letterSpacing: -1 }}>USD {fmt(grandTotal)}</span></div>
          </Card>
        </>)}
        {/* SUMMARY */}
        {tab === "summary" && (
          <Card style={{ padding: "24px 28px", marginBottom: 16 }}>
            <div className="card-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 24 }}>
              <div style={{ background: T.bg, borderRadius: 12, padding: 18, textAlign: "center" }}><div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: T.txt3, marginBottom: 6 }}>Total Base</div><div style={{ fontSize: 26, fontWeight: 800, color: T.navy, fontVariantNumeric: "tabular-nums" }}>${fmt(baseTotal)}</div><div style={{ fontSize: 11, color: T.txt3, marginTop: 4 }}>Client payments collected</div></div>
              <div style={{ background: T.bg, borderRadius: 12, padding: 18, textAlign: "center" }}><div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: T.txt3, marginBottom: 6 }}>Total Commission</div><div style={{ fontSize: 26, fontWeight: 800, color: T.ok, fontVariantNumeric: "tabular-nums" }}>${fmt(grandTotal)}</div><div style={{ fontSize: 11, color: T.txt3, marginTop: 4 }}>Including premio de vendas</div></div>
            </div>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5, color: T.txt3, marginBottom: 12 }}>Breakdown</div>
            {d.commissions.map((c, i) => { const pct = (c.amount / grandTotal) * 100; return (
              <div key={i} style={{ marginBottom: 10 }}><div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}><span style={{ color: T.txt2 }}>{c.client} — {c.fatura}</span><span style={{ fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>${fmt(c.amount)} ({pct.toFixed(1)}%)</span></div><div style={{ height: 6, background: T.bg, borderRadius: 3, overflow: "hidden" }}><div style={{ height: "100%", width: `${pct}%`, background: `linear-gradient(90deg, ${T.mint}, ${T.mintDark})`, borderRadius: 3, transition: "width 0.5s" }} /></div></div>
            ); })}
            <div style={{ marginTop: 10 }}><div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}><span style={{ color: T.warn }}>Premio de Vendas</span><span style={{ fontWeight: 600, color: T.warn }}>${fmt(d.premio.amount)} ({((d.premio.amount / grandTotal) * 100).toFixed(1)}%)</span></div><div style={{ height: 6, background: T.warnBg, borderRadius: 3, overflow: "hidden" }}><div style={{ height: "100%", width: `${(d.premio.amount / grandTotal) * 100}%`, background: `linear-gradient(90deg, #F59E0B, ${T.warn})`, borderRadius: 3 }} /></div></div>
            <div style={{ background: T.okBg, borderRadius: 10, padding: "12px 16px", fontSize: 11, color: T.ok, lineHeight: 1.6, marginTop: 16 }}>Commission on payments collected by Marluvas during February 2026. Export of services — exempt from Costa Rica VAT.</div>
          </Card>
        )}
        {/* BANK */}
        {tab === "bank" && (
          <Card style={{ padding: "24px 28px", marginBottom: 16 }}>
            <Lbl>Wire Transfer Details</Lbl>
            <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "8px 20px", fontSize: 13, marginTop: 8 }}>
              {[["Bank", d.bank.name, false], ["Address", d.bank.address, false], ["SWIFT", d.bank.swift, true], ["ABA", d.bank.aba, true], ["Account", d.bank.account, true], ["Beneficiary", d.bank.beneficiary, false], ["Amount", `USD ${fmt(grandTotal)}`, true]].map(([l, v, m], i) => (
                <React.Fragment key={i}><div style={{ fontWeight: 600, color: T.txt3, fontSize: 12 }}>{l}:</div><div style={{ fontWeight: 600, color: T.txt1, fontFamily: m ? T.mono : "inherit" }}>{v}</div></React.Fragment>
              ))}
            </div>
            <div style={{ marginTop: 20, padding: "12px 16px", background: T.bg, borderRadius: 10, fontSize: 11, color: T.txt3, lineHeight: 1.7 }}>Bank selection is variable per invoice — CEO chooses destination bank. Confirm beneficiary details before initiating wire transfer.</div>
          </Card>
        )}
        {/* Compliance + Signature + Footer */}
        <Card style={{ padding: "14px 18px", marginBottom: 16, borderLeft: `3px solid ${T.mint}` }}><div style={{ fontSize: 11, color: T.txt2, lineHeight: 1.7 }}>This is a commercial invoice for international services. It is <strong>not</strong> a Costa Rica electronic tax document nor a Brazilian <em>nota fiscal</em>. Invoice number follows MWT internal sequence.</div></Card>
        <SignatureGate sig={d.signature} />
        <Footer text={`Invoice ${d.number} · ${d.date} · Muito Work Limitada · Commercial invoice for international services`} />
      </div>
    </div>
  );
}
