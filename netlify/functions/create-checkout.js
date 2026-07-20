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
        
        // Product price mapping matching actual Obsidian project prices
        const prices = {
            // AI Video Ads (from AI-Video-Ad-Agency.md)
            'video-basic': 50000,        // $500 single ad
            'video-pro': 150000,        // $1,500 premium single
            'video-campaign': 300000,    // $3,000 package
            // Pet Portraits (from Pet-AI-Art-Business.md)
            'pet-digital': 3500,         // $35 digital download
            'pet-print': 4500,           // $45 8×10 print
            'pet-canvas': 7500,        // $75 16×20 canvas
            'pet-gift': 11000           // $110 24×30 premium
        };
        
        const productNames = {
            'video-basic': 'AI Video Ad — Basic (Single)',
            'video-pro': 'AI Video Ad — Professional (Single)',
            'video-campaign': 'AI Video Ad — Campaign Package',
            'pet-digital': 'Pet Portrait — Digital Download',
            'pet-print': 'Pet Portrait — 8×10″ Framed Print',
            'pet-canvas': 'Pet Portrait — 16×20″ Canvas Wrap',
            'pet-gift': 'Pet Portrait — 24×30″ Premium Package'
        };
        
        const amount = prices[product] || 50000;
        const name = productNames[product] || 'Hightower Marketing Service';

        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [{
                price_data: {
                    currency: 'usd',
                    product_data: { name: name },
                    unit_amount: amount,
                },
                quantity: 1,
            }],
            mode: 'payment',
            success_url: `${process.env.URL || 'https://hightower-marketing.com'}/checkout-video.html?success=true&product=${product}`,
            cancel_url: `${process.env.URL || 'https://hightower-marketing.com'}/checkout-video.html?canceled=true`,
            customer_email: email || undefined,
            metadata: {
                product: product,
                source: 'hightower-marketing.com',
                project: product.startsWith('pet') ? 'Pet-AI-Art-Business' : 'AI-Video-Ad-Agency'
            }
        });

        return { statusCode: 200, headers, body: JSON.stringify({ url: session.url }) };
    } catch (error) {
        console.error('Stripe error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
