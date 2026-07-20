// Simple order submission handler
// Currently just logs the order — connect to email/DB later
exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    };

    if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };

    try {
        // Parse multipart form data (Netlify parses this automatically)
        const body = JSON.parse(event.body);
        
        console.log('ORDER RECEIVED:', JSON.stringify(body, null, 2));
        
        // TODO: Send email notification, save to database, create Obsidian task
        // For now, just log and return success
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({ success: true, message: 'Order logged' })
        };
    } catch (error) {
        console.error('Order error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: 'Failed to process order' })
        };
    }
};
