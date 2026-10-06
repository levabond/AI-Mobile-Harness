public protocol ProfileLoading: Sendable {
  func loadProfile() async throws -> Profile
}

@MainActor
public final class ProfileDetailsViewModel {
  public private(set) var state: ProfileDetailsState = .loading

  private let loader: any ProfileLoading

  public init(loader: any ProfileLoading) {
    self.loader = loader
  }

  public func load() async {
    state = .loading

    do {
      state = .content(try await loader.loadProfile())
    } catch {
      state = .failure(message: "Profile could not be loaded.")
    }
  }

  public func retry() async {
    await load()
  }
}
