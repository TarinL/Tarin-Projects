using MySqlConnector;

public class DbConnectionFactory
{
    private readonly string _cs;

    public DbConnectionFactory(IConfiguration cfg)
        => _cs = cfg.GetConnectionString("Default")!;

    public MySqlConnection Create()
        => new MySqlConnection(_cs);
}

