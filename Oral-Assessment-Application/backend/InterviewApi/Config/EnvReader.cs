namespace InterviewApi.Config;

class EnvReader
{
    public static void Load(string filepath)
    {
        if (!File.Exists(filepath))
        {
            throw new FileNotFoundException($"File with filepath {filepath} does not exist");
        }
        foreach (var line in File.ReadAllLines(filepath))
        {
            if (string.IsNullOrWhiteSpace(line) || line.StartsWith("#"))
                continue;
            var parts = line.Split("=", 2);
            
            if (parts.Length != 2)
                continue;
            
            var key = parts[0].Trim();
            var value = parts[1].Trim();

            Environment.SetEnvironmentVariable(key, value);
        }
    }
}