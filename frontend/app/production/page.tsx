async function getProductionData() {
  // Replace this URL with your actual backend or Next.js local API endpoint
  const res = await fetch('http://backend:8000/production/inventory/', { 
    cache: 'no-store' // Ensures you always get the latest data from the DB
  });

  if (!res.ok) {
    throw new Error('Failed to fetch Production data');
  } 
  return res.json();
}

export default async function Production() {
  const productionData = await getProductionData();
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold">Welcome to the Production Page</h1>
              {/* Inventory Table Container */}
        <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wider text-gray-500">
                <tr>
                  <th scope="col" className="px-6 py-4">Material Number</th>
                  <th scope="col" className="px-6 py-4">Material Name</th>
                  <th scope="col" className="px-6 py-4">Lot Number</th>
                  <th scope="col" className="px-6 py-4 text-right">Quantity</th>
                  <th scope="col" className="px-6 py-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {productionData.map((item : any) => {
                  const isOutOfStock = item.quantity === 0;

                  return (
                    <tr key={item.material_number} className="hover:bg-gray-50 transition-colors">
                      {/* Material Number */}
                      <td className="whitespace-nowrap px-6 py-4 font-mono font-medium text-gray-900">
                        {item.material_number}
                      </td>
                      
                      {/* Material Name */}
                      <td className="whitespace-nowrap px-6 py-4 capitalize text-gray-700">
                        {item.material_name}
                      </td>
                      
                      {/* Lot Number */}
                      <td className="whitespace-nowrap px-6 py-4 font-mono text-gray-500">
                        {item.lot_number}
                      </td>
                      
                      {/* Quantity & Unit */}
                      <td className="whitespace-nowrap px-6 py-4 text-right font-semibold text-gray-900">
                        {item.quantity} <span className="text-xs font-normal text-gray-500">{item.unit}</span>
                      </td>
                      
                      {/* Status Indicator Badges */}
                      <td className="whitespace-nowrap px-6 py-4 text-center">
                        {isOutOfStock ? (
                          <span className="inline-flex items-center rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 border border-red-200">
                            Out of Stock
                          </span>
                        ) : (
                          <span className="inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700 border border-green-200">
                            In Stock
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
      </div>
      <p className="mt-4 text-lg text-gray-600">This is the production page of the application.</p>
    </main>
  );
}