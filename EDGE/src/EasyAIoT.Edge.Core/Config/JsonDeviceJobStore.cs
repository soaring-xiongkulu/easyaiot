using System.Text.Json;
using EasyAIoT.Edge.Abstractions.Config;

namespace EasyAIoT.Edge.Core.Config;

public sealed class JsonDeviceJobStore : IDeviceJobStore
{
    private readonly List<DeviceJobConfig> _jobs = new();
    private readonly string _filePath;
    private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNameCaseInsensitive = true, WriteIndented = true };

    public JsonDeviceJobStore(string filePath) => _filePath = filePath;

    public IReadOnlyList<DeviceJobConfig> GetAll() => _jobs.ToList();

    public DeviceJobConfig? GetByJobId(string jobId) =>
        _jobs.FirstOrDefault(j => j.JobId == jobId);

    public void Upsert(DeviceJobConfig job)
    {
        var index = _jobs.FindIndex(j => j.JobId == job.JobId);
        if (index >= 0)
            _jobs[index] = job;
        else
            _jobs.Add(job);
        Save();
    }

    public void Remove(string jobId)
    {
        _jobs.RemoveAll(j => j.JobId == jobId);
        Save();
    }

    public void ReplaceAll(IEnumerable<DeviceJobConfig> jobs)
    {
        _jobs.Clear();
        _jobs.AddRange(jobs);
        Save();
    }

    public void Load()
    {
        if (!File.Exists(_filePath))
            return;
        var json = File.ReadAllText(_filePath);
        var loaded = JsonSerializer.Deserialize<List<DeviceJobConfig>>(json, _jsonOptions);
        if (loaded != null)
        {
            _jobs.Clear();
            _jobs.AddRange(loaded);
        }
    }

    private void Save()
    {
        var dir = Path.GetDirectoryName(_filePath);
        if (!string.IsNullOrEmpty(dir))
            Directory.CreateDirectory(dir);
        File.WriteAllText(_filePath, JsonSerializer.Serialize(_jobs, _jsonOptions));
    }
}
