async function getProducts() {
  // Replace this URL with your actual backend or Next.js local API endpoint
  const res = await fetch('http://backend:8000/products/ledger/', { 
    cache: 'no-store' // Ensures you always get the latest data from the DB
  });

  if (!res.ok) {
    throw new Error('Failed to fetch Product data');
  }

  return res.json();
}

export default async function Home() {
  const products = await getProducts(); // Fetch product data
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold">Welcome to the Home Page</h1>
      <table cellPadding="10" style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr style={{ backgroundColor: '#f4f4f4' }}>
              <th>Product Code</th>
              <th>Product Name</th>
              <th>customers</th>
              <th>part_number</th>
              <th>Quantity</th>
            </tr>
          </thead>
          <tbody>
            {products.map((item: any, index: any) => (
              <tr key={item.id || index}>
                <td>{item.product_code}</td>
                <td>{item.product_name}</td>
                <td>{item.customers}</td>
                <td>{item.part_number}</td> 
                <td>{item.quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      <p className="mt-4 text-lg text-gray-600">This is the main landing page of the application.</p>
    </main>
  );
}