// Client para conectar a builder.mwt.one
export const fetchBuilderArtifacts = async () => {
  const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjo0ODk4MjQ2MTkwLCJpYXQiOjE3NzYxODIxOTAsImp0aSI6ImYxNDc5NDY3MTI5ZjQ2ZmNhYmRjYTEyOWZhZWY1ZmVkIiwidXNlcl9pZCI6IjEifQ.O2XAua47zQxq7Wct3V_0H28lK9U1_5322cnCS6LNrXA';
  try {
    const res = await fetch(`https://builder.mwt.one/api/artefactos/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    if (!res.ok) {
      console.error('Error al obtener lista de artefactos de Builder');
      return [];
    }
    const data = await res.json();
    return data;
  } catch (err) {
    console.error('Exception fetching artifacts list from Builder:', err);
    return [];
  }
};

export const fetchBuilderArtifactStructure = async (id: string | number) => {
  const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjo0ODk4MjQ2MTkwLCJpYXQiOjE3NzYxODIxOTAsImp0aSI6ImYxNDc5NDY3MTI5ZjQ2ZmNhYmRjYTEyOWZhZWY1ZmVkIiwidXNlcl9pZCI6IjEifQ.O2XAua47zQxq7Wct3V_0H28lK9U1_5322cnCS6LNrXA';
  try {
    const res = await fetch(`https://builder.mwt.one/api/artefactos/${id}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    if (!res.ok) {
      console.error(`Error al obtener estructura para artefacto ${id}`);
      return null;
    }
    const data = await res.json();
    return data;
  } catch (err) {
    console.error(`Exception fetching structure for artifact ${id}:`, err);
    return null;
  }
};
