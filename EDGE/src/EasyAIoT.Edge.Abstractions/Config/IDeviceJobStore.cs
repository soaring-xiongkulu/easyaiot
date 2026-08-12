using EasyAIoT.Edge.Abstractions.Config;

namespace EasyAIoT.Edge.Abstractions.Config;

public interface IDeviceJobStore
{
    IReadOnlyList<DeviceJobConfig> GetAll();

    DeviceJobConfig? GetByJobId(string jobId);

    void Upsert(DeviceJobConfig job);

    void Remove(string jobId);

    void ReplaceAll(IEnumerable<DeviceJobConfig> jobs);
}
