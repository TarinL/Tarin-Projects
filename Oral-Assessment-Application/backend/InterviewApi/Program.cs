using Amazon;
using Amazon.ECS;
using Dapper;
using InterviewApi.Config;
using InterviewApi.Data;
using InterviewApi.Services;

public class Program
{
    public static void Main(string[] args)
    {
        if (File.Exists(".env")) {
            EnvReader.Load(".env");
        }

        DefaultTypeMap.MatchNamesWithUnderscores = true;
    
        var builder = WebApplication.CreateBuilder(args);
        
        builder.Configuration.AddEnvironmentVariables();

        builder.Services.AddSingleton<DbConnectionFactory>();
        builder.Services.AddControllers();
        builder.Services.AddScoped<IInterviewRepository, InterviewRepository>();
        builder.Services.AddHttpClient<AssessmentGenerator>();
        // Scoped (not singleton): it depends on the typed-HttpClient AssessmentGenerator,
        // whose HttpClient is managed per-resolution by IHttpClientFactory.
        builder.Services.AddScoped<AssessmentParser>();
        builder.Services.AddSingleton<IAmazonECS>(_ =>
            new AmazonECSClient(RegionEndpoint.GetBySystemName(
                builder.Configuration["Ecs:Region"] ?? "ap-southeast-2")));
        builder.Services.AddEndpointsApiExplorer(); 
        builder.Services.AddSwaggerGen(o =>
            o.SupportNonNullableReferenceTypes()
        );
        
        builder.Services.AddCors(options =>
        {
            options.AddDefaultPolicy(policy =>
            {
                policy.AllowAnyOrigin()
                    .AllowAnyMethod()
                    .AllowAnyHeader();
            });
        });
        
        var app = builder.Build();
        
        if (app.Environment.IsDevelopment())
        {
            app.UseSwagger();
            app.UseSwaggerUI();
        }
        
        app.UseCors();
        app.MapControllers();
        app.Run();
    }
}
