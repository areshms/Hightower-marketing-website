const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    };

    if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
    if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

    try {
        const { product, email } = JSON.parse(event.body);

        // Product catalog. One-time products use mode='payment'. 're-data-refinery-monthly' is a subscription.
        const catalog = {
            // AI Video Ads (from AI-Video-Ad-Agency.md)
            'video-basic': { amount: 50000, name: 'AI Video Ad — Basic (Single)', mode: 'payment', project: 'AI-Video-Ad-Agency' },
            'video-pro': { amount: 150000, name: 'AI Video Ad — Professional (Single)', mode: 'payment', project: 'AI-Video-Ad-Agency' },
            'video-campaign': { amount: 300000, name: 'AI Video Ad — Campaign Package', mode: 'payment', project: 'AI-Video-Ad-Agency' },
            // Pet Portraits (from Pet-AI-Art-Business.md)
            'pet-digital': { amount: 3500, name: 'Pet Portrait — Digital Download', mode: 'payment', project: 'Pet-AI-Art-Business' },
            'pet-print': { amount: 4500, name: 'Pet Portrait — 8×10″ Framed Print', mode: 'payment', project: 'Pet-AI-Art-Business' },
            'pet-canvas': { amount: 7500, name: 'Pet Portrait — 16×20″ Canvas Wrap', mode: 'payment', project: 'Pet-AI-Art-Business' },
            'pet-gift': { amount: 11000, name: 'Pet Portrait — 24×30″ Premium Package', mode: 'payment', project: 'Pet-AI-Art-Business' },
            // RE Data Refinery monthly subscription
            're-data-refinery-monthly': {
                amount: 30000,
                name: 'RE Data Refinery — Columbus OH Monthly Sheet Access',
                mode: 'subscription',
                project: 'RE-Data-Refinery',
                recurring: { interval: 'month', interval_count: 1 }
            }
        };

        const item = catalog[product] || catalog['video-pro'];
        const baseUrl = process.env.URL || 'https://hightower-marketing.com';

        let sessionParams = {
            payment_method_types: ['card'],
            line_items: [{
                price_data: {
                    currency: 'usd',
                    product_data: { name: item.name },
                    unit_amount: item.amount,
                },
                quantity: 1,
            }],
            mode: item.mode,
            success_url: `${baseUrl}/re-data-refinery.html?success=true`,
            cancel_url: `${baseUrl}/re-data-refinery.html?canceled=true`,
            customer_email: email || undefined,
            metadata: {
                product: product,
                source: 'hightower-marketing.com',
                project: item.project
            }
        };

        if (item.mode === 'subscription' && item.recurring) {
            sessionParams.line_items[0].price_data.recurring = {
                interval: item.recurring.interval,
                interval_count: item.recurring.interval_count
            };
            // Subscription success URL can include session_id if needed for webhook-free lookups
            sessionParams.success_url = `${baseUrl}/re-data-refinery-success.html?success=true&session_id={CHECKOUT_SESSION_ID}`;
            sessionParams.cancel_url = `${baseUrl}/re-data-refinery.html?canceled=true`;
        }

        const session = await stripe.checkout.sessions.create(sessionParams);

        return { statusCode: 200, headers, body: JSON.stringify({ url: session.url }) };
    } catch (error) {
        console.error('Stripe error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
