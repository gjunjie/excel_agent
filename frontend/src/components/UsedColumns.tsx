interface UsedColumnsProps {
  columns: string[];
}

export default function UsedColumns({ columns }: UsedColumnsProps) {
  if (!columns || columns.length === 0) {
    return <div className="empty-state">No columns used</div>;
  }

  return (
    <div className="used-columns">
      {columns.map((col) => (
        <span key={col} className="column-badge">
          {col}
        </span>
      ))}
    </div>
  );
}

