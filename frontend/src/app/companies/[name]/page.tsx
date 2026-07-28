"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function CompanyProfile() {
  const { name } = useParams();
  const companyName = decodeURIComponent(name as str);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/companies/${companyName}`)
      .then(res => res.json())
      .then(data => setData(data))
      .catch(err => console.error(err));
  }, [companyName]);

  if (!data) return (
    <div className="container">
      <nav className="nav">
        <h1 className="title-glow" style={{ fontSize: '2rem' }}>PIP Nexus</h1>
        <div><Link href="/">Dashboard</Link></div>
      </nav>
      <p>Loading intelligence data...</p>
    </div>
  );

  return (
    <div className="container">
      <nav className="nav">
        <h1 className="title-glow" style={{ fontSize: '2rem' }}>PIP Nexus</h1>
        <div>
          <Link href="/">Dashboard</Link>
        </div>
      </nav>

      <main>
        <div className="glass-panel" style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 className="title-glow" style={{ fontSize: '3rem', marginBottom: '8px' }}>{data.name}</h1>
            <p style={{ color: 'var(--text-muted)' }}>Average CTC: <span style={{ color: 'var(--text-main)', fontWeight: 'bold' }}>{data.average_ctc || 'N/A'}</span></p>
          </div>
          {data.tier && (
             <span className="badge" style={{ fontSize: '1rem', padding: '8px 16px' }}>{data.tier}</span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '40px' }}>
          <section>
            <h2 style={{ marginBottom: '24px', fontSize: '1.5rem', color: 'var(--text-main)' }}>Frequently Tested Skills</h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
              {data.top_skills?.length === 0 ? <p style={{color: 'var(--text-muted)'}}>No skill data available.</p> : null}
              {data.top_skills?.map((skill: string, idx: number) => (
                <span key={idx} className="badge" style={{ background: 'var(--surface)', color: 'var(--text-main)', border: '1px solid var(--border)' }}>
                  {skill}
                </span>
              ))}
            </div>
          </section>

          <section>
            <h2 style={{ marginBottom: '24px', fontSize: '1.5rem', color: 'var(--text-main)' }}>Historical Interview Questions</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {data.questions?.length === 0 ? <p style={{color: 'var(--text-muted)'}}>No questions on record.</p> : null}
              {data.questions?.map((q: any, idx: number) => (
                <div key={idx} className="glass-panel" style={{ padding: '20px' }}>
                  <p style={{ fontSize: '1.1rem', lineHeight: '1.6', marginBottom: '12px' }}>"{q.text}"</p>
                  {q.difficulty && (
                    <span className="badge" style={{ 
                      background: q.difficulty === 'Hard' ? 'rgba(239, 68, 68, 0.1)' : q.difficulty === 'Medium' ? 'rgba(234, 179, 8, 0.1)' : 'rgba(34, 197, 94, 0.1)',
                      color: q.difficulty === 'Hard' ? '#ef4444' : q.difficulty === 'Medium' ? '#eab308' : '#22c55e',
                      borderColor: 'transparent'
                    }}>
                      {q.difficulty}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
