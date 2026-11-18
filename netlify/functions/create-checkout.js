const https = require('https');
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
                name: 'RE Data Refinery — Ohio 18-City Sheet Access (Monthly)',
                mode: 'subscription',
                project: 'RE-Data-Refinery',
                recurring: { interval: 'month', interval_count: 1 }
            },
            // SB Grants Database monthly subscription
            'grants-db-monthly': {
                amount: 3000,
                name: 'SB Grants Database — Monthly',
                mode: 'subscription',
                project: 'SB-Grants-Database',
                recurring: { interval: 'month', interval_count: 1 },
                success_url: '/grants-db-success.html?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url: '/grants-db.html?canceled=true'
            }
        };

        const item = catalog[product];
  if (!item) return { statusCode: 400, body: JSON.stringify({ error: `Unknown product: ${product}` }) };
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
            success_url: item.success_url ? `${baseUrl}${item.success_url}` : (item.mode === 'subscription' ? `${baseUrl}/re-data-refinery-success.html?success=true&session_id={CHECKOUT_SESSION_ID}` : `${baseUrl}/order-success.html?session_id={CHECKOUT_SESSION_ID}`),
            cancel_url: item.cancel_url ? `${baseUrl}${item.cancel_url}` : `${baseUrl}/re-data-refinery.html?canceled=true`,
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
            if (!item.success_url) {
                sessionParams.success_url = `${baseUrl}/re-data-refinery-success.html?success=true&session_id={CHECKOUT_SESSION_ID}`;
            }
            sessionParams.cancel_url = item.cancel_url ? `${baseUrl}${item.cancel_url}` : `${baseUrl}/re-data-refinery.html?canceled=true`;
        }

        const session = await stripe.checkout.sessions.create(sessionParams);

        // Sale notify (fire-and-forget, never blocks checkout): AgentMail -> ares.hms@icloud.com
        if (item.project === 'RE-Data-Refinery' || item.project === 'SB-Grants-Database') {
            try {
                const buyer = email || (session.customer_email || 'not provided at checkout');
                const mailBody = JSON.stringify({
                    to: ['ares.hms@icloud.com'],
                    subject: 'SALE: ' + item.project + ' subscription started',
                    text: 'A buyer just started: ' + item.name + '\n' +
                        'Buyer email: ' + buyer + '\n' +
                        'Stripe session: ' + session.id + '\n' +
                        'Deliver sheet access within one business day. Verify payment in the Stripe dashboard.'
                });
                const mailReq = https.request({
                    hostname: 'api.agentmail.to',
                    path: '/v0/inboxes/hightower-marketing-outreach%40agentmail.to/messages', method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + process.env.AGENTMAIL_API_KEY,
                               'Accept': 'application/json',
                               'Content-Type': 'application/json',
                               'Content-Length': Buffer.byteLength(mailBody) },
                    timeout: 5000 }, () => {});
                mailReq.on('error', () => {});
                mailReq.on('timeout', () => mailReq.destroy());
                mailReq.end(mailBody);
            } catch (e) { /* notification must never break checkout */ }
        }

        return { statusCode: 200, headers, body: JSON.stringify({ url: session.url }) };
    } catch (error) {
        console.error('Stripe error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
