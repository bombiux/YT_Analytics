import pandas as pd

def get_top_5_videos_per_channel_to_csv(csv_file_path, output_csv_path):
    """
    Reads a CSV file and creates a new CSV with the 5 videos with the highest view counts for each channel.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        output_csv_path (str): Path for the output CSV file
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Group by ChannelName and get top 5 videos for each channel
    all_top_videos = []
    
    for channel in df['ChannelName'].unique():
        channel_data = df[df['ChannelName'] == channel]
        top_5_for_channel = channel_data.nlargest(5, 'ViewCount')
        
        # Add rank within channel
        top_5_for_channel = top_5_for_channel.copy()
        top_5_for_channel['RankWithinChannel'] = range(1, 6)
        
        all_top_videos.append(top_5_for_channel)
    
    # Concatenate all top videos
    result_df = pd.concat(all_top_videos, ignore_index=True)
    
    # Select and reorder columns
    result_df = result_df[['ChannelName', 'RankWithinChannel', 'VideoType', 'Title', 'ViewCount', 'Date', 'VideoID', 'LikeCount', 'PublishedAt']]
    
    # Save to CSV
    result_df.to_csv(output_csv_path, index=False)
    
    return result_df

# File paths
input_csv = 'all_videos_report.csv'
output_csv = 'top_5_videos_per_channel.csv'

# Get top 5 videos per channel and save to CSV
result = get_top_5_videos_per_channel_to_csv(input_csv, output_csv)

print(f"Top 5 videos per channel saved to {output_csv}")
print("\nFirst few rows of the result:")
print(result.head(10))