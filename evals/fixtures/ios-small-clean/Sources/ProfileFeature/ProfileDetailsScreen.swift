#if canImport(SwiftUI)
  import SwiftUI

  @available(iOS 16.0, macOS 13.0, *)
  public struct ProfileDetailsScreen: View {
    private let state: ProfileDetailsState
    private let retryAction: () -> Void

    public init(state: ProfileDetailsState, retryAction: @escaping () -> Void) {
      self.state = state
      self.retryAction = retryAction
    }

    public var body: some View {
      Group {
        switch state {
        case .loading:
          ProgressView("Loading profile")
            .accessibilityIdentifier("profile.loading")
        case .content(let profile):
          List {
            LabeledContent("Name", value: profile.displayName)
            LabeledContent("Handle", value: profile.handle)
            Text(profile.biography)
          }
          .accessibilityIdentifier("profile.content")
        case .failure(let message):
          VStack(spacing: 12) {
            Image(systemName: "person.crop.circle.badge.exclamationmark")
              .font(.largeTitle)
            Text("Unable to load profile")
              .font(.headline)
            Text(message)
            Button("Retry", action: retryAction)
              .accessibilityIdentifier("profile.retry")
          }
          .padding()
          .accessibilityIdentifier("profile.error")
        }
      }
      .navigationTitle("Profile")
    }
  }

  @available(iOS 16.0, macOS 13.0, *)
  public struct ProfileDetailsScreenPreview: PreviewProvider {
    public static var previews: some View {
      NavigationStack {
        ProfileDetailsScreen(
          state: .content(
            Profile(
              displayName: "Avery Morgan",
              handle: "@avery",
              biography: "Mobile engineer and trail runner."
            )
          ),
          retryAction: {}
        )
      }
    }
  }
#endif
