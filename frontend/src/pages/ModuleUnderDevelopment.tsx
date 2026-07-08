export const ModuleUnderDevelopment = ({ title }: { title: string }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#e2e8f0' }}>{title}</h1>
      <p style={{ color: '#94a3b8', fontSize: '1.25rem' }}>Module under development</p>
    </div>
  );
};
