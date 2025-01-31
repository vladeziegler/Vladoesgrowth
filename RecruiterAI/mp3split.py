from pydub import AudioSegment
import os
import math

def split_mp3(input_file, output_dir, segment_length_minutes=10):
    """
    Split a long MP3 file into smaller segments.
    
    Parameters:
    input_file (str): Path to the input MP3 file
    output_dir (str): Directory to save the output files
    segment_length_minutes (int): Length of each segment in minutes
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load the audio file
    print(f"Loading audio file: {input_file}")
    audio = AudioSegment.from_mp3(input_file)
    
    # Calculate segment length in milliseconds
    segment_length_ms = segment_length_minutes * 60 * 1000
    total_length_ms = len(audio)
    
    # Calculate number of segments
    num_segments = math.ceil(total_length_ms / segment_length_ms)
    
    # Get the base filename without extension
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    
    print(f"Splitting into {num_segments} segments...")
    
    # Split and export segments
    for i in range(num_segments):
        start_time = i * segment_length_ms
        end_time = min((i + 1) * segment_length_ms, total_length_ms)
        
        # Extract segment
        segment = audio[start_time:end_time]
        
        # Generate output filename
        output_filename = f"{base_filename}_part{i+1:03d}.mp3"
        output_path = os.path.join(output_dir, output_filename)
        
        # Export segment
        print(f"Exporting segment {i+1}/{num_segments}: {output_filename}")
        segment.export(output_path, format="mp3")
    
    print("Splitting complete!")

# Example usage
if __name__ == "__main__":
    # Configuration
    input_file = "RecruiterAI/voiceSample.mp3"  # Replace with your input file path
    output_dir = "RecruiterAI/split_segments"   # Output directory name
    segment_length = 1.5            # Length of each segment in minutes
    
    # Split the file
    split_mp3(input_file, output_dir, segment_length)