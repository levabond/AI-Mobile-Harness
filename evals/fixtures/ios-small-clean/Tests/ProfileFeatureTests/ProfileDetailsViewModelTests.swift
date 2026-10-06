import XCTest

@testable import ProfileFeature

private enum LoaderError: Error {
  case unavailable
}

private actor SequenceLoader: ProfileLoading {
  private var results: [Result<Profile, Error>]

  init(results: [Result<Profile, Error>]) {
    self.results = results
  }

  func loadProfile() async throws -> Profile {
    try results.removeFirst().get()
  }
}

final class ProfileDetailsViewModelTests: XCTestCase {
  @MainActor
  func testInitialStateIsLoading() {
    let loader = SequenceLoader(results: [])
    let viewModel = ProfileDetailsViewModel(loader: loader)

    XCTAssertEqual(viewModel.state, .loading)
  }

  @MainActor
  func testSuccessfulLoadProducesContent() async {
    let profile = Profile(displayName: "Avery", handle: "@avery", biography: "Engineer")
    let loader = SequenceLoader(results: [.success(profile)])
    let viewModel = ProfileDetailsViewModel(loader: loader)

    await viewModel.load()

    XCTAssertEqual(viewModel.state, .content(profile))
  }

  @MainActor
  func testFailureProducesRecoverableErrorAndRetryCanSucceed() async {
    let profile = Profile(displayName: "Avery", handle: "@avery", biography: "Engineer")
    let loader = SequenceLoader(results: [.failure(LoaderError.unavailable), .success(profile)])
    let viewModel = ProfileDetailsViewModel(loader: loader)

    await viewModel.load()
    XCTAssertEqual(viewModel.state, .failure(message: "Profile could not be loaded."))

    await viewModel.retry()
    XCTAssertEqual(viewModel.state, .content(profile))
  }

  func testDetailsRouteIsStable() {
    XCTAssertEqual(ProfileRoute.details.rawValue, "profile-details")
  }

  #if canImport(SwiftUI)
    @MainActor
    func testScreenContractCanBeConstructedForEveryState() {
      let profile = Profile(displayName: "Avery", handle: "@avery", biography: "Engineer")

      _ = ProfileDetailsScreen(state: .loading, retryAction: {})
      _ = ProfileDetailsScreen(state: .content(profile), retryAction: {})
      _ = ProfileDetailsScreen(state: .failure(message: "Unavailable"), retryAction: {})
    }
  #endif
}
