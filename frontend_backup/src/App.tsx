// src/App.tsx
import { useEffect, useState } from 'react';
import { Grid } from './components/Grid';
import {
  fetchInitialState,
  makeStep,
  makeSteps,
  restartSim,
  buyUpgrade,
} from './api/client';
import type { GameState, ShopItemState } from './types/index';

// ---------- Style ----------
const pageStyle: React.CSSProperties = {
  display: 'flex', gap: '1.5rem', padding: '1.5rem', alignItems: 'flex-start',
  flexWrap: 'wrap', justifyContent: 'center',
};
const panelStyle: React.CSSProperties = {
  backgroundColor: 'rgba(11, 11, 30, 0.7)', border: '1px solid var(--border-color)',
  borderRadius: '16px', boxShadow: '0 4px 30px rgba(0,0,0,0.4)',
  backdropFilter: 'blur(5px)', padding: '1.25rem',
};
const buttonStyle: React.CSSProperties = {
  backgroundColor: 'var(--accent-primary)', color: '#fff', border: 'none',
  padding: '10px 14px', borderRadius: '8px', cursor: 'pointer',
  fontSize: '0.95rem', fontWeight: 'bold', transition: 'all 0.2s ease',
};
const rowStyle: React.CSSProperties = {
  display: 'flex', justifyContent: 'space-between', gap: '0.5rem',
  fontSize: '0.9rem', padding: '2px 0',
};

// ---------- Pasek postępu (bateria / plecak) ----------
const Bar = ({ pct, color }: { pct: number; color: string }) => (
  <div style={{ background: '#222', borderRadius: '6px', height: '12px', width: '100%', overflow: 'hidden' }}>
    <div style={{ width: `${Math.max(0, Math.min(100, pct))}%`, height: '100%', background: color, transition: 'width 0.3s ease' }} />
  </div>
);

// ---------- Panel sklepu ----------
const ShopPanel = ({
  items, onBuy, disabled,
}: { items: ShopItemState[]; onBuy: (id: string) => void; disabled: boolean }) => (
  <div style={{ ...panelStyle, width: '320px' }}>
    <h3 style={{ marginTop: 0 }}>🛒 Sklep z ulepszeniami</h3>
    {items.map((it) => {
      const mats = it.next_cost_materials
        ? Object.entries(it.next_cost_materials).map(([m, q]) => `${m}×${q}`).join(', ')
        : '';
      return (
        <div key={it.id} style={{ borderTop: '1px solid var(--border-color)', padding: '8px 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong>{it.name}</strong>
            <span style={{ opacity: 0.7 }}>lvl {it.level}/{it.max_level}</span>
          </div>
          <div style={{ fontSize: '0.8rem', opacity: 0.75, margin: '2px 0' }}>{it.description}</div>
          {it.is_maxed ? (
            <div style={{ color: '#5fd35f', fontWeight: 'bold', fontSize: '0.85rem' }}>MAX</div>
          ) : (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.82rem' }}>
                💰 ${it.next_cost_money}{mats ? ` + ${mats}` : ''}
              </span>
              <button
                style={{
                  ...buttonStyle, padding: '5px 12px', fontSize: '0.82rem',
                  opacity: it.affordable && !disabled ? 1 : 0.4,
                  cursor: it.affordable && !disabled ? 'pointer' : 'not-allowed',
                  backgroundColor: it.affordable ? 'var(--accent-primary)' : '#555',
                }}
                onClick={() => onBuy(it.id)}
                disabled={!it.affordable || disabled}
              >
                Kup
              </button>
            </div>
          )}
        </div>
      );
    })}
  </div>
);

function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchInitialState().then(setGameState).catch((e) => console.error('Network error:', e));
  }, []);

  const run = async (fn: () => Promise<GameState>) => {
    if (isLoading) return;
    setIsLoading(true);
    try { setGameState(await fn()); } catch (e) { console.error(e); } finally { setIsLoading(false); }
  };

  const handleBuy = async (id: string) => {
    if (isLoading) return;
    setIsLoading(true);
    try {
      const res = await buyUpgrade(id);
      setMessage(res.message);
      setGameState(await fetchInitialState());
    } catch (e) { console.error(e); } finally { setIsLoading(false); }
  };

  if (!gameState) {
    return <div style={{ color: 'var(--text-secondary)', padding: '2rem' }}>Awaiting Signal from Mars...</div>;
  }

  const a = gameState.agent;
  const env = gameState.environment;
  const battPct = a.max_battery > 0 ? (a.battery / a.max_battery) * 100 : 0;
  const fillPct = a.capacity > 0 ? (a.current_weight / a.capacity) * 100 : 0;
  const volPct = a.volume_capacity > 0 ? (a.current_volume / a.volume_capacity) * 100 : 0;
  const battColor = battPct > 50 ? '#4caf50' : battPct > 20 ? '#e0b020' : '#e04040';

  // Zliczanie zawartości plecaka wg typu
  const inv: Record<string, number> = {};
  a.inventory.forEach((m) => { inv[m] = (inv[m] || 0) + 1; });

  return (
    <main>
      <header style={{ textAlign: 'center', padding: '1rem' }}>
        <h1 style={{ margin: 0, textTransform: 'uppercase' }}>Mission Control</h1>
        <p style={{ margin: 0, color: 'var(--text-secondary)', opacity: 0.8 }}>
          Mars Rover — Problem Plecakowy &amp; Sklep
        </p>
      </header>

      <div style={pageStyle}>
        {/* LEWA: mapa + sterowanie */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignItems: 'center' }}>
          <Grid gameState={gameState} />
          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button style={{ ...buttonStyle, opacity: isLoading ? 0.6 : 1 }} onClick={() => run(makeStep)} disabled={isLoading}>
              {isLoading ? '…' : 'Krok ▶'}
            </button>
            <button style={{ ...buttonStyle, opacity: isLoading ? 0.6 : 1 }} onClick={() => run(() => makeSteps(10))} disabled={isLoading}>
              Krok ×10 ⏩
            </button>
            <button style={{ ...buttonStyle, backgroundColor: '#a23', opacity: isLoading ? 0.6 : 1 }} onClick={() => run(restartSim)} disabled={isLoading}>
              Restart ⟳
            </button>
          </div>
        </div>

        {/* ŚRODEK: HUD */}
        <div style={{ ...panelStyle, width: '300px' }}>
          <h3 style={{ marginTop: 0 }}>📡 Telemetria</h3>
          <div style={rowStyle}><span>Status</span><strong>{a.status}</strong></div>
          <div style={rowStyle}><span>Krok / Pogoda</span><span>{env.step_counter} · {env.weather.replace(/_/g, ' ')}</span></div>

          <div style={{ margin: '8px 0 2px' }}>Bateria: {a.battery.toFixed(1)} / {a.max_battery.toFixed(0)}</div>
          <Bar pct={battPct} color={battColor} />

          <div style={{ margin: '8px 0 2px' }}>Plecak — waga: {a.current_weight.toFixed(1)} / {a.capacity.toFixed(0)} kg</div>
          <Bar pct={fillPct} color="#4a90d9" />

          <div style={{ margin: '8px 0 2px' }}>Plecak — objętość: {a.current_volume.toFixed(1)} / {a.volume_capacity.toFixed(0)} l</div>
          <Bar pct={volPct} color="#9a6cd9" />

          <div style={{ ...rowStyle, marginTop: '10px' }}><span>💰 Budżet</span><strong>${a.money.toFixed(1)}</strong></div>
          <div style={rowStyle}>
            <span>Ładunek</span>
            <span>{Object.keys(inv).length ? Object.entries(inv).map(([m, q]) => `${m}:${q}`).join(', ') : '—'}</span>
          </div>
          <div style={rowStyle}><span>Ulepszenia</span>
            <span>{Object.entries(a.upgrade_levels).map(([k, v]) => `${k[0].toUpperCase()}${v}`).join(' ')}</span>
          </div>
          <div style={{ ...rowStyle, fontSize: '0.8rem', opacity: 0.7 }}><span>NN</span><span>{a.nn_thought}</span></div>
        </div>

        {/* PRAWA: sklep */}
        <ShopPanel items={gameState.shop} onBuy={handleBuy} disabled={isLoading} />
      </div>

      {message && (
        <div style={{ textAlign: 'center', color: 'var(--accent-secondary)', padding: '0.5rem' }}>{message}</div>
      )}
    </main>
  );
}

export default App;
