#!/usr/bin/env node

// Simple test script to verify YouTube downloader functionality
const ytdl = require('@distube/ytdl-core');

async function testYouTube() {
    const testUrl = 'https://youtu.be/EUq1L6XoZvU?si=qPToLdYGwTeF3vZq';
    
    console.log('Testing YouTube URL:', testUrl);
    
    try {
        // Test URL validation
        console.log('URL validation:', ytdl.validateURL(testUrl));
        
        // Test getting video info
        console.log('Getting video info...');
        const info = await ytdl.getInfo(testUrl);
        
        console.log('Success! Video info:');
        console.log('- Title:', info.videoDetails.title);
        console.log('- Duration:', info.videoDetails.lengthSeconds, 'seconds');
        console.log('- Author:', info.videoDetails.author.name);
        console.log('- Views:', info.videoDetails.viewCount);
        
        // Test available formats
        const audioFormats = ytdl.filterFormats(info.formats, 'audioonly');
        const videoFormats = ytdl.filterFormats(info.formats, 'videoonly');
        
        console.log('- Audio formats available:', audioFormats.length);
        console.log('- Video formats available:', videoFormats.length);
        
        console.log('\n✅ YouTube downloader is working correctly!');
        
    } catch (error) {
        console.error('❌ Error:', error.message);
        console.error('Full error:', error);
        process.exit(1);
    }
}

testYouTube();
