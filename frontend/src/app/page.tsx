"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function Home() {
  const [skills, setSkills] = useState([]);
  const [companies, setCompanies] = useState([]);

  useEffect(() => {
    // Fetch Top Skills
    fetch('http://localhost:8000/api/skills/top?limit=6')
      .then(res => res.json())
      .then(data => setSkills(data))
      .catch(err => console.error(err));

    // Fetch Companies
    fetch('http://localhost:8000/api/companies')
      .then(res => res.json())
      .then(data => setCompanies(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="container">
      <nav className="nav">
        <h1 className="title-glow" style={{ fontSize: '2rem' }}>PIP Nexus</h1>
        <div>
          <Link href="/">Dashboard</Link>
        </div>
      </nav>

      <main>
        <section style={{ marginBottom: '60px' }}>
          <h2 style={{ marginBottom: '24px', fontSize: '1.5rem', color: 'var(--text-main)' }}>
            High ROI Skills <span style={{ color: 'var(--text-muted)', fontSize: '1rem', fontWeight: 'normal' }}>(Ranked by Degree Centrality)</span>
          </h2>
          <div className="grid">
            {skills.length === 0 ? <p>Loading graph analytics...</p> : null}
            {skills.map((s: any, idx) => (
              <div key={idx} className="glass-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <h3 style={{ fontSize: '1.25rem' }}>{s.skill}</h3>
                  <span className="badge">Rank #{idx + 1}</span>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Domain: {s.domain}</p>
                <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ flex: 1, background: 'rgba(255,255,255,0.1)', height: '6px', borderRadius: '3px' }}>
                    <div style={{ width: `${Math.min((s.score / skills[0].score) * 100, 100)}%`, background: 'var(--primary)', height: '100%', borderRadius: '3px' }}></div>
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{s.score} pts</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 style={{ marginBottom: '24px', fontSize: '1.5rem', color: 'var(--text-main)' }}>Company Intelligence Profiles</h2>
          <div className="grid">
            {companies.length === 0 ? <p>Loading companies...</p> : null}
            {companies.map((c: any, idx) => (
              <Link href={`/companies/${c.name}`} key={idx} style={{ textDecoration: 'none', color: 'inherit' }}>
                <div className="glass-panel" style={{ cursor: 'pointer' }}>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '8px' }}>{c.name}</h3>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    {c.tier && <span className="badge" style={{ background: 'rgba(168, 85, 247, 0.1)', color: 'var(--secondary)', borderColor: 'rgba(168, 85, 247, 0.2)' }}>{c.tier}</span>}
                  </div>
                  {c.average_ctc && <p style={{ color: 'var(--text-muted)' }}>Avg CTC: <strong style={{ color: 'var(--text-main)' }}>{c.average_ctc}</strong></p>}
                </div>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
