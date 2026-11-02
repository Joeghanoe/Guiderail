public sealed class WebhookFunction(EventTypeMapper mapper)
{
    public string Map(string externalType) => mapper.ToInternal(externalType);
}
