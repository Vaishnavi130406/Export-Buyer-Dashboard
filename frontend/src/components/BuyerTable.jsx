function BuyerTable({ buyers }) {
  return (
    <table className="buyer-table">
      <thead>
        <tr>
          <th>Company</th>
          <th>Country</th>
          <th>Website</th>
          <th>Email</th>
        </tr>
      </thead>

      <tbody>
        {buyers.map((buyer, index) => (
          <tr key={index}>
            <td>{buyer.company_name}</td>
            <td>{buyer.country}</td>
            <td>
              <a
                href={buyer.website}
                target="_blank"
                rel="noreferrer"
              >
                {buyer.website}
              </a>
            </td>

            <td>
              {buyer.email && buyer.email !== ""
                ? buyer.email
                : (
                  <span style={{ color: "red" }}>
                    Email Not Found
                  </span>
                )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default BuyerTable;