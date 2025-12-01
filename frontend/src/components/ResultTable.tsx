interface ResultTableProps {
  result: any[] | null;
  columns: string[] | null;
}

export default function ResultTable({ result, columns }: ResultTableProps) {
  if (!result || result.length === 0) {
    return <div className="empty-state">No results to display</div>;
  }

  // If we have columns, use them; otherwise infer from first row keys
  const tableColumns = columns || (result.length > 0 ? Object.keys(result[0]) : []);

  return (
    <div className="table-container">
      <table className="result-table">
        <thead>
          <tr>
            {tableColumns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.map((row, idx) => (
            <tr key={idx}>
              {tableColumns.map((col) => (
                <td key={col}>{String(row[col] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

